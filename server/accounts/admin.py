from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserLoginHistory


class UserLoginHistoryInline(admin.TabularInline):
    model = UserLoginHistory
    extra = 0
    readonly_fields = ('login_datetime', 'ip_address', 'user_agent', 'device_type', 'login_status')
    can_delete = False
    max_num = 10
    verbose_name = _('Login History')
    verbose_name_plural = _('Login History')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'is_two_factor_enabled')
    list_filter = ('role', 'is_staff', 'is_active', 'is_two_factor_enabled')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Security'), {'fields': ('is_two_factor_enabled', 'last_login_ip')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'last_login_ip')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = [UserLoginHistoryInline]


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_datetime', 'ip_address', 'device_type', 'login_status')
    list_filter = ('login_status', 'login_datetime', 'device_type')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('user', 'login_datetime', 'ip_address', 'user_agent', 'device_type', 'login_status')
    date_hierarchy = 'login_datetime'
