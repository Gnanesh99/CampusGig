from django.urls import path
from .views import (
    PaymentInitiateView,
    PaymentCheckoutView,
    PaymentVerifyView,
    RazorpayWebhookView,
)

app_name = 'payments'

urlpatterns = [
    path('<int:pk>/initiate/', PaymentInitiateView.as_view(), name='initiate'),
    path('<int:pk>/checkout/', PaymentCheckoutView.as_view(), name='checkout'),
    path('verify/', PaymentVerifyView.as_view(), name='verify'),
    path('webhook/', RazorpayWebhookView.as_view(), name='webhook'),
]
