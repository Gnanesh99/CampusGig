import logging
import json
import razorpay
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Payment
from .services import create_razorpay_order

logger = logging.getLogger(__name__)

class PaymentInitiateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk)

        # Only the payer/employer associated with that Payment may initiate the payment.
        if payment.payer != request.user:
            raise PermissionDenied("You are not authorized to initiate this payment.")

        # Only allow order creation when Payment.status is Pending.
        if payment.status != 'Pending':
            return JsonResponse({'error': 'Payment is not pending.'}, status=400)

        try:
            # If Payment.razorpay_order_id already exists, it is handled inside create_razorpay_order
            # which returns early. But create_razorpay_order returns the ID or Razorpay dict depending on implementation.
            # We implemented create_razorpay_order to return the ID if it already exists, or the Razorpay order dict if newly created.
            # To be safe, we rely on the saved payment.razorpay_order_id
            create_razorpay_order(payment)
            
            # Re-fetch or rely on updated payment object
            payment.refresh_from_db()
            
            return JsonResponse({
                'razorpay_order_id': payment.razorpay_order_id,
                'amount': payment.amount,
                'currency': 'INR'
            })
        except Exception as e:
            logger.error(f"Error initiating payment {payment.id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render
from django.conf import settings

class PaymentCheckoutView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk)

        if payment.payer != request.user:
            raise PermissionDenied("You are not authorized to checkout this payment.")

        if payment.status != 'Pending':
            return render(request, 'payments/checkout.html', {'error': 'Payment is no longer pending.'})

        try:
            create_razorpay_order(payment)
            payment.refresh_from_db()
        except Exception as e:
            logger.error(f"Failed to initiate order for checkout {payment.id}: {e}")
            return render(request, 'payments/checkout.html', {'error': 'Failed to initiate payment gateway.'})

        context = {
            'payment': payment,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount_in_paise': int(payment.amount * 100),
            'currency': 'INR',
        }
        return render(request, 'payments/checkout.html', context)

class PaymentVerifyView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Allow reading from form data or JSON body
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        if not razorpay_payment_id:
            try:
                data = json.loads(request.body)
                razorpay_payment_id = data.get('razorpay_payment_id')
                razorpay_order_id = data.get('razorpay_order_id')
                razorpay_signature = data.get('razorpay_signature')
            except json.JSONDecodeError:
                pass

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        # Find the Payment using the Razorpay order ID
        payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)

        # Verify that the authenticated user is the Payment payer
        if payment.payer != request.user:
            raise PermissionDenied("You are not authorized to verify this payment.")

        # Prevent an already Paid Payment from being processed again
        if payment.status == 'Paid':
            return JsonResponse({'status': 'Already Paid'})

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            # Verify the Razorpay signature using the Razorpay SDK
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Only after successful signature verification:
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'Paid'
            payment.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'status', 'updated_at'])
            
            return JsonResponse({'status': 'success'})

        except razorpay.errors.SignatureVerificationError:
            # If signature verification fails, do not mark the Payment as Paid.
            # Keeping the Payment Pending as instructed (or leaving it alone).
            logger.error(f"Signature verification failed for payment {payment.id}")
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error during payment verification {payment.id}: {e}")
            return JsonResponse({'error': 'Server error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    def post(self, request, *args, **kwargs):
        webhook_signature = request.headers.get('X-Razorpay-Signature') or request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        if not webhook_signature:
            return JsonResponse({'error': 'Missing signature header'}, status=400)

        raw_body = request.body
        body_str = raw_body.decode('utf-8')

        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None) or settings.RAZORPAY_KEY_SECRET

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_webhook_signature(body_str, webhook_signature, webhook_secret)
        except razorpay.errors.SignatureVerificationError:
            logger.error("Razorpay webhook signature verification failed.")
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        except Exception as e:
            logger.error(f"Error during webhook signature verification: {e}")
            return JsonResponse({'error': 'Verification error'}, status=400)

        try:
            event_data = json.loads(body_str)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        event = event_data.get('event')
        payload = event_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')

        if order_id:
            payment = Payment.objects.filter(razorpay_order_id=order_id).first()
            if payment:
                if event == 'payment.captured':
                    # Idempotency: only update if status is not already Paid
                    if payment.status != 'Paid':
                        payment.status = 'Paid'
                        if payment_id:
                            payment.razorpay_payment_id = payment_id
                        payment.save(update_fields=['status', 'razorpay_payment_id', 'updated_at'])

                        # Mark the linked Assignment as Completed
                        assignment = payment.assignment
                        if assignment.status != 'Completed':
                            assignment.status = 'Completed'
                            assignment.completed_at = timezone.now()
                            assignment.save(update_fields=['status', 'completed_at'])
                elif event == 'payment.failed':
                    # Idempotency: do not corrupt an already Paid payment
                    if payment.status != 'Paid':
                        payment.status = 'Failed'
                        if payment_id:
                            payment.razorpay_payment_id = payment_id
                        payment.save(update_fields=['status', 'razorpay_payment_id', 'updated_at'])

        return JsonResponse({'status': 'ok'}, status=200)
