from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from applications.models import Application, Assignment
from gigs.models import Category, Gig


# ---------------------------------------------------------------------------
# Shared fixture helper
# ---------------------------------------------------------------------------

def _make_world():
    """
    Creates two independent employer/student pairs, each with their own Gig,
    Application, and Assignment.  Returns both assignments so cross-ownership
    tests can be written easily.
    """
    employer_a = User.objects.create_user(email='employer_a@test.com', password='pass')
    employer_b = User.objects.create_user(email='employer_b@test.com', password='pass')
    student_a = User.objects.create_user(email='student_a@test.com', password='pass')
    student_b = User.objects.create_user(email='student_b@test.com', password='pass')

    category = Category.objects.create(name='Writing', slug='writing')

    # Gig / Application / Assignment belonging to employer_a & student_a
    gig_a = Gig.objects.create(
        title='Article writing',
        description='Write an article',
        category=category,
        poster=employer_a,
        budget=Decimal('200.00'),
        location='Remote',
    )
    app_a = Application.objects.create(
        gig=gig_a,
        applicant=student_a,
        cover_letter='I can write.',
        status='hired',
    )
    assignment_a = Assignment.objects.create(
        application=app_a,
        employer=employer_a,
        student=student_a,
        status='Submitted',
    )

    # Gig / Application / Assignment belonging to employer_b & student_b
    gig_b = Gig.objects.create(
        title='Blog post',
        description='Write a blog',
        category=category,
        poster=employer_b,
        budget=Decimal('150.00'),
        location='Remote',
    )
    app_b = Application.objects.create(
        gig=gig_b,
        applicant=student_b,
        cover_letter='I can blog.',
        status='hired',
    )
    assignment_b = Assignment.objects.create(
        application=app_b,
        employer=employer_b,
        student=student_b,
        status='Assigned',
    )

    return {
        'employer_a': employer_a,
        'employer_b': employer_b,
        'student_a': student_a,
        'student_b': student_b,
        'assignment_a': assignment_a,
        'assignment_b': assignment_b,
    }


# ---------------------------------------------------------------------------
# Test 5 – Student B cannot start Student A's assignment → 403
# ---------------------------------------------------------------------------

class StudentCrossAssignmentAuthorizationTest(TestCase):

    def setUp(self):
        self.world = _make_world()

    def test_student_b_cannot_start_student_a_assignment(self):
        """
        Student B is logged in, but tries to start an Assignment that belongs
        to Student A.  The view must return HTTP 403.
        """
        assignment_a = self.world['assignment_a']
        # Force assignment_a to 'Assigned' so it's a valid start candidate
        assignment_a.status = 'Assigned'
        assignment_a.save(update_fields=['status'])

        self.client.login(email='student_b@test.com', password='pass')
        url = reverse('student-assignment-start', kwargs={'pk': assignment_a.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)

        # Assignment must not have changed
        assignment_a.refresh_from_db()
        self.assertEqual(assignment_a.status, 'Assigned')


# ---------------------------------------------------------------------------
# Test 6 – Employer B cannot reject Employer A's assignment → 403
# ---------------------------------------------------------------------------

class EmployerCrossAssignmentAuthorizationTest(TestCase):

    def setUp(self):
        self.world = _make_world()

    def test_employer_b_cannot_reject_employer_a_assignment(self):
        """
        Employer B is logged in, but tries to reject an Assignment that belongs
        to Employer A.  The view must return HTTP 403.
        """
        assignment_a = self.world['assignment_a']
        # assignment_a is already 'Submitted' from setUp

        self.client.login(email='employer_b@test.com', password='pass')
        url = reverse('employer-assignment-reject', kwargs={'pk': assignment_a.pk})
        response = self.client.post(url, data={'employer_feedback': 'Not good'})

        self.assertEqual(response.status_code, 403)

        # Assignment must not have changed
        assignment_a.refresh_from_db()
        self.assertEqual(assignment_a.status, 'Submitted')
        self.assertFalse(assignment_a.employer_feedback)


# ---------------------------------------------------------------------------
# Shared single-pair fixture for workflow tests
# ---------------------------------------------------------------------------

def _make_single_pair(status='In Progress'):
    """
    One employer, one student, one gig, one application, one assignment.
    Assignment.save() auto-creates the Payment.
    """
    employer = User.objects.create_user(email='emp@test.com', password='pass')
    student = User.objects.create_user(email='stu@test.com', password='pass')
    category = Category.objects.create(name='Dev', slug='dev')
    gig = Gig.objects.create(
        title='Build a site',
        description='Make a website',
        category=category,
        poster=employer,
        budget=Decimal('300.00'),
        location='Remote',
    )
    app = Application.objects.create(
        gig=gig,
        applicant=student,
        cover_letter='On it.',
        status='hired',
    )
    assignment = Assignment.objects.create(
        application=app,
        employer=employer,
        student=student,
        status=status,
    )
    return {
        'employer': employer,
        'student': student,
        'assignment': assignment,
    }


# ---------------------------------------------------------------------------
# Submission validation tests
# ---------------------------------------------------------------------------

class SubmissionValidationTest(TestCase):

    def setUp(self):
        self.world = _make_single_pair(status='In Progress')

    def test_empty_submission_is_rejected_and_assignment_stays_in_progress(self):
        """No text and no file → 200 with error, assignment stays In Progress."""
        assignment = self.world['assignment']
        self.client.login(email='stu@test.com', password='pass')

        url = reverse('student-assignment-submit', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={})  # no text, no file

        # View re-renders the form with an error message (not a redirect)
        self.assertEqual(response.status_code, 200)

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'In Progress')
        self.assertIsNone(assignment.submission_text)

    def test_valid_text_submission_transitions_to_submitted(self):
        """Providing submission_text → assignment transitions to Submitted."""
        assignment = self.world['assignment']
        self.client.login(email='stu@test.com', password='pass')

        url = reverse('student-assignment-submit', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={'submission_text': 'Here is my work.'})

        self.assertRedirects(response, reverse('student-assignment-list'))

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Submitted')
        self.assertEqual(assignment.submission_text, 'Here is my work.')

    def test_student_cannot_submit_when_status_is_not_in_progress(self):
        """Submitting when status is 'Assigned' (not 'In Progress') must redirect without saving."""
        # Force status back to Assigned
        assignment = self.world['assignment']
        assignment.status = 'Assigned'
        assignment.save(update_fields=['status'])

        self.client.login(email='stu@test.com', password='pass')
        url = reverse('student-assignment-submit', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={'submission_text': 'Should not save.'})

        # The view redirects away without changing state
        self.assertRedirects(response, reverse('student-assignment-list'))

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Assigned')
        self.assertIsNone(assignment.submission_text)


# ---------------------------------------------------------------------------
# Reject / resubmit flow tests
# ---------------------------------------------------------------------------

class RejectResubmitFlowTest(TestCase):

    def setUp(self):
        self.world = _make_single_pair(status='Submitted')

    def test_rejection_transitions_to_in_progress_and_saves_feedback(self):
        """Employer rejection: Submitted → In Progress, employer_feedback saved."""
        assignment = self.world['assignment']
        self.client.login(email='emp@test.com', password='pass')

        url = reverse('employer-assignment-reject', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={'employer_feedback': 'Please revise section 2.'})

        self.assertRedirects(response, reverse('employer-assignment-list'))

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'In Progress')
        self.assertEqual(assignment.employer_feedback, 'Please revise section 2.')

    def test_student_can_resubmit_after_rejection(self):
        """After rejection (In Progress), student can submit again → Submitted."""
        assignment = self.world['assignment']
        # Simulate rejection
        assignment.status = 'In Progress'
        assignment.employer_feedback = 'Please revise.'
        assignment.save(update_fields=['status', 'employer_feedback'])

        self.client.login(email='stu@test.com', password='pass')
        url = reverse('student-assignment-submit', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={'submission_text': 'Revised and resubmitted.'})

        self.assertRedirects(response, reverse('student-assignment-list'))

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Submitted')
        self.assertEqual(assignment.submission_text, 'Revised and resubmitted.')

    def test_employer_cannot_reject_when_status_is_not_submitted(self):
        """Rejecting a non-Submitted assignment must redirect without state change."""
        assignment = self.world['assignment']
        assignment.status = 'In Progress'
        assignment.save(update_fields=['status'])

        self.client.login(email='emp@test.com', password='pass')
        url = reverse('employer-assignment-reject', kwargs={'pk': assignment.pk})
        response = self.client.post(url, data={'employer_feedback': 'Bad'})

        self.assertRedirects(response, reverse('employer-assignment-list'))

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'In Progress')
        self.assertIsNone(assignment.employer_feedback)


# ---------------------------------------------------------------------------
# Employer accept flow tests
# ---------------------------------------------------------------------------

class EmployerAcceptFlowTest(TestCase):

    def setUp(self):
        self.world = _make_single_pair(status='Submitted')

    def test_accept_redirects_to_payment_checkout(self):
        """
        Accepting a Submitted assignment must redirect to payments:checkout.
        Payment and Assignment must remain unchanged (not yet Paid/Completed).
        """
        from payments.models import Payment

        assignment = self.world['assignment']
        payment = Payment.objects.get(assignment=assignment)

        self.client.login(email='emp@test.com', password='pass')
        url = reverse('employer-assignment-accept', kwargs={'pk': assignment.pk})
        response = self.client.post(url)

        expected_redirect = reverse('payments:checkout', kwargs={'pk': payment.pk})
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

        # Assignment must still be Submitted — only the webhook completes it
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Submitted')
        self.assertIsNone(assignment.completed_at)

        # Payment must still be Pending — only the webhook marks it Paid
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Pending')

    def test_employer_cannot_accept_when_status_is_not_submitted(self):
        """Accepting a non-Submitted assignment must redirect without side-effects."""
        from payments.models import Payment

        assignment = self.world['assignment']
        assignment.status = 'In Progress'
        assignment.save(update_fields=['status'])
        payment = Payment.objects.get(assignment=assignment)

        self.client.login(email='emp@test.com', password='pass')
        url = reverse('employer-assignment-accept', kwargs={'pk': assignment.pk})
        response = self.client.post(url)

        self.assertRedirects(response, reverse('employer-assignment-list'))

        # No state changes
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'In Progress')
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Pending')
