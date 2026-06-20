from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['email','username','full_name','currency','is_premium','is_staff','is_active','date_joined']
    list_filter   = ['is_premium','currency','is_staff','is_active']
    search_fields = ['email','username','first_name','last_name']
    ordering      = ['-date_joined']
    readonly_fields = ['date_joined','last_login','password_display']

    fieldsets = UserAdmin.fieldsets + (
        ('CashTrail Info', {'fields': ('avatar','currency','monthly_budget','bio','phone','is_premium')}),
        ('Security Info',  {'fields': ('password_display',), 'classes': ('collapse',)}),
    )

    def full_name(self, obj):
        return obj.get_full_name() or '—'
    full_name.short_description = 'Name'

    def password_display(self, obj):
        return format_html(
            '<code style="background:#f5f5f5;padding:4px 8px;border-radius:4px;font-size:12px">{}</code>',
            obj.password
        )
    password_display.short_description = 'Password Hash (read-only)'

from .models import UserRegistrationLog

@admin.register(UserRegistrationLog)
class RegLogAdmin(admin.ModelAdmin):
    list_display  = ['user_email','registered_at','ip_address','password_algo']
    search_fields = ['user__email','ip_address']
    readonly_fields = ['user','registered_at','ip_address','user_agent','password_algo']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
