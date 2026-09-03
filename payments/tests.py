

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import razorpay
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from applications.models import Application, Assignment
from gigs.models import Category, Gig
from payments.models import Payment


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def _make_world():
    """Return a dict of objects used by every webhook test."""
    employer = User.objects.create_user(email='employer@test.com', password='pass')
    student = User.objects.create_user(email='student@test.com', password='pass')

    category = Category.objects.create(name='Design', slug='design')
    gig = Gig.objects.create(
        title='Logo design',
        description='Need a logo',
        category=category,
        poster=employer,
        budget=Decimal('500.00'),
        location='Remote',
    )
    application = Application.objects.create(
        gig=gig,
        applicant=student,
        cover_letter='I can do this.',
        status='hired',
    )
    # Assignment.save() automatically creates the Payment
    assignment = Assignment.objects.create(
        application=application,
        employer=employer,
        student=student,
        status='Submitted',
    )
    payment = Payment.objects.get(assignment=assignment)
    # Simulate that a Razorpay order has been created
    payment.razorpay_order_id = 'order_test_abc123'
    payment.save(update_fields=['razorpay_order_id'])

    return {
        'employer': employer,
        'student': student,
        'assignment': assignment,
        'payment': payment,
    }


def _make_webhook_payload(order_id, payment_id, event='payment.captured'):
    """Construct the minimal Razorpay webhook JSON body."""
    return json.dumps({
        'event': event,
        'payload': {
            'payment': {
                'entity': {
                    'id': payment_id,
                    'order_id': order_id,
                }
            }
        }
    })


WEBHOOK_URL = reverse('payments:webhook')


# ---------------------------------------------------------------------------
# Test 1 – Missing X-Razorpay-Signature → 400
# ---------------------------------------------------------------------------

class WebhookMissingSignatureTest(TestCase):

    def test_missing_signature_header_returns_400(self):
        response = self.client.post(
            WEBHOOK_URL,
            data='{}',
            content_type='application/json',
            # Intentionally omit HTTP_X_RAZORPAY_SIGNATURE
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())


# ---------------------------------------------------------------------------
# Test 2 – Invalid webhook signature → 400
# ---------------------------------------------------------------------------

class WebhookInvalidSignatureTest(TestCase):

    def setUp(self):
        _make_world()

    @patch('payments.views.razorpay.Client')
    def test_invalid_signature_returns_400(self, MockClient):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.utility.verify_webhook_signature.side_effect = (
            razorpay.errors.SignatureVerificationError('Bad signature', None, None)
        )

        response = self.client.post(
            WEBHOOK_URL,
            data='{}',
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='bad_signature',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        # Payment must not be mutated
        payment = Payment.objects.first()
        self.assertEqual(payment.status, 'Pending')


# ---------------------------------------------------------------------------
# Test 3 – Valid payment.captured → Payment=Paid, Assignment=Completed,
#           completed_at is set
# ---------------------------------------------------------------------------

class WebhookPaymentCapturedTest(TestCase):

    def setUp(self):
        self.world = _make_world()

    @patch('payments.views.razorpay.Client')
    def test_payment_captured_marks_payment_paid_and_assignment_completed(self, MockClient):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        # verify_webhook_signature returns None on success (no exception)
        mock_client.utility.verify_webhook_signature.return_value = None

        payment = self.world['payment']
        assignment = self.world['assignment']
        body = _make_webhook_payload(payment.razorpay_order_id, 'pay_live_xyz')

        response = self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='valid_sig',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('status'), 'ok')

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Paid')
        self.assertEqual(payment.razorpay_payment_id, 'pay_live_xyz')

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Completed')
        self.assertIsNotNone(assignment.completed_at)


# ---------------------------------------------------------------------------
# Test 4 – payment.captured is idempotent (second identical call does nothing)
# ---------------------------------------------------------------------------

class WebhookIdempotencyTest(TestCase):

    def setUp(self):
        self.world = _make_world()

    @patch('payments.views.razorpay.Client')
    def test_duplicate_payment_captured_is_idempotent(self, MockClient):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.utility.verify_webhook_signature.return_value = None

        payment = self.world['payment']
        assignment = self.world['assignment']
        body = _make_webhook_payload(payment.razorpay_order_id, 'pay_live_xyz')

        # Send the same webhook twice
        for _ in range(2):
            self.client.post(
                WEBHOOK_URL,
                data=body,
                content_type='application/json',
                HTTP_X_RAZORPAY_SIGNATURE='valid_sig',
            )

        payment.refresh_from_db()
        assignment.refresh_from_db()

        # State must be exactly what we expect after one processing
        self.assertEqual(payment.status, 'Paid')
        self.assertEqual(assignment.status, 'Completed')
        # verify_webhook_signature was called both times (signature is always verified)
        self.assertEqual(mock_client.utility.verify_webhook_signature.call_count, 2)
