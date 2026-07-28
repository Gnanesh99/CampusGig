from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import User, StudentProfile


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_verified_college_email')
    list_filter = ('is_staff', 'is_active', 'is_moderator', 'is_admin', 'is_verified_college_email')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_moderator', 'is_admin', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('is_verified_college_email',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff')
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college', 'department', 'year', 'phone_number')
    search_fields = ('user__email', 'college', 'department')


admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
