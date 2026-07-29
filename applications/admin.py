from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('gig', 'applicant', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('applicant__username', 'gig__title')
