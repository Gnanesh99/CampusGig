from django.contrib import admin

from .models import Application,Assignment


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('gig', 'applicant', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('applicant__username', 'gig__title')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('application', 'employer', 'student', 'status', 'hired_at')
    list_filter = ('status',)
    search_fields = ('employer__email', 'student__email', 'application__gig__title')