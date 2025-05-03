from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Supplier, AccountPayable, PayableTransaction, PaymentReminder


class PayableInline(admin.TabularInline):
    model = AccountPayable
    extra = 0
    fields = ('payment_number', 'transaction_date', 'due_date', 'amount', 'status')
    readonly_fields = ('payment_number',)
    can_delete = False
    show_change_link = True
    max_num = 10


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'phone', 'email', 'payment_terms', 'total_outstanding', 'is_active')
    list_filter = ('is_active', 'payment_terms', 'created_at')
    search_fields = ('name', 'arabic_name', 'phone', 'email', 'tax_number')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'total_outstanding')
    fieldsets = (
        (None, {'fields': ('name', 'arabic_name', 'is_active')}),
        (_('Contact Information'), {'fields': ('contact_person', 'phone', 'email', 'address')}),
        (_('Financial Information'), {'fields': ('tax_number', 'payment_terms', 'total_outstanding')}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [PayableInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PayableTransactionInline(admin.TabularInline):
    model = PayableTransaction
    extra = 0
    fields = ('transaction_type', 'amount', 'transaction_date', 'reference')
    can_delete = False
    show_change_link = True
    max_num = 10


class PaymentReminderInline(admin.TabularInline):
    model = PaymentReminder
    extra = 0
    fields = ('reminder_type', 'reminder_date', 'sent', 'sent_date')
    readonly_fields = ('reminder_date',)
    can_delete = False
    max_num = 5


@admin.register(AccountPayable)
class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'supplier', 'bank', 'transaction_date', 'due_date', 'amount', 'status', 'days_until_due')
    list_filter = ('status', 'transaction_date', 'due_date', 'bank')
    search_fields = ('payment_number', 'check_number', 'supplier__name', 'invoice_number', 'notes')
    readonly_fields = ('payment_number', 'created_by', 'created_at', 'updated_at', 'days_until_due', 'last_reminder_date')
    date_hierarchy = 'transaction_date'
    fieldsets = (
        (None, {'fields': ('payment_number', 'supplier', 'bank', 'status')}),
        (_('Transaction Details'), {'fields': ('transaction_date', 'due_date', 'amount', 'check_number', 'days_until_due')}),
        (_('Invoice Information'), {'fields': ('invoice_number', 'invoice_date')}),
        (_('Reminder Information'), {'fields': ('last_reminder_date',)}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [PayableTransactionInline, PaymentReminderInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PayableTransaction)
class PayableTransactionAdmin(admin.ModelAdmin):
    list_display = ('payable', 'transaction_type', 'amount', 'transaction_date', 'reference')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('payable__payment_number', 'reference', 'notes')
    readonly_fields = ('created_by', 'created_at')
    date_hierarchy = 'transaction_date'
    fieldsets = (
        (None, {'fields': ('payable', 'transaction_type')}),
        (_('Transaction Details'), {'fields': ('amount', 'transaction_date', 'reference')}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at')}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ('payable', 'reminder_type', 'reminder_date', 'sent', 'sent_date', 'sent_by')
    list_filter = ('reminder_type', 'sent', 'reminder_date')
    search_fields = ('payable__payment_number', 'payable__supplier__name', 'notes')
    readonly_fields = ('reminder_date',)
    date_hierarchy = 'reminder_date'
    fieldsets = (
        (None, {'fields': ('payable', 'reminder_type', 'reminder_date')}),
        (_('Status'), {'fields': ('sent', 'sent_date', 'sent_by')}),
        (_('Additional Information'), {'fields': ('notes',)}),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.sent and not obj.sent_by:
            obj.sent_by = request.user
        super().save_model(request, obj, form, change)
