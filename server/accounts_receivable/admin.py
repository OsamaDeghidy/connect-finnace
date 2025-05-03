from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Bank, Client, AccountReceivable, ReceivableTransaction


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'branch', 'swift_code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'arabic_name', 'branch', 'swift_code')
    fieldsets = (
        (None, {'fields': ('name', 'arabic_name', 'is_active')}),
        (_('Bank Details'), {'fields': ('branch', 'swift_code')}),
        (_('Contact Information'), {'fields': ('contact_person', 'phone', 'email', 'address')}),
    )


class ReceivableInline(admin.TabularInline):
    model = AccountReceivable
    extra = 0
    fields = ('receipt_number', 'transaction_date', 'due_date', 'amount', 'status')
    readonly_fields = ('receipt_number',)
    can_delete = False
    show_change_link = True
    max_num = 10


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'phone', 'email', 'total_outstanding', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'arabic_name', 'phone', 'email', 'tax_number')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'total_outstanding')
    fieldsets = (
        (None, {'fields': ('name', 'arabic_name', 'is_active')}),
        (_('Contact Information'), {'fields': ('contact_person', 'phone', 'email', 'address')}),
        (_('Financial Information'), {'fields': ('tax_number', 'credit_limit', 'total_outstanding')}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [ReceivableInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReceivableTransactionInline(admin.TabularInline):
    model = ReceivableTransaction
    extra = 0
    fields = ('transaction_type', 'amount', 'transaction_date', 'reference')
    can_delete = False
    show_change_link = True
    max_num = 10


@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'client', 'bank', 'transaction_date', 'due_date', 'amount', 'status')
    list_filter = ('status', 'transaction_date', 'due_date', 'bank')
    search_fields = ('receipt_number', 'check_number', 'client__name', 'notes')
    readonly_fields = ('receipt_number', 'created_by', 'created_at', 'updated_at')
    date_hierarchy = 'transaction_date'
    fieldsets = (
        (None, {'fields': ('receipt_number', 'client', 'bank', 'status')}),
        (_('Transaction Details'), {'fields': ('transaction_date', 'due_date', 'amount', 'check_number')}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [ReceivableTransactionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReceivableTransaction)
class ReceivableTransactionAdmin(admin.ModelAdmin):
    list_display = ('receivable', 'transaction_type', 'amount', 'transaction_date', 'reference')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('receivable__receipt_number', 'reference', 'notes')
    readonly_fields = ('created_by', 'created_at')
    date_hierarchy = 'transaction_date'
    fieldsets = (
        (None, {'fields': ('receivable', 'transaction_type')}),
        (_('Transaction Details'), {'fields': ('amount', 'transaction_date', 'reference')}),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at')}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
