from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'payer', 'payee', 'amount', 'status','razorpay_order_id','razorpay_payment_id', 'created_at')
    list_filter = ('status',)
    search_fields = ('payer__email', 'payee__email', 'assignment__id')
