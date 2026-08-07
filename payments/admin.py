from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'payer', 'payee', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('payer__username', 'payee__username', 'assignment__id')
