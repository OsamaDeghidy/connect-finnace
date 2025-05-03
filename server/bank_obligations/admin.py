from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import BankObligation, ObligationPayment


class ObligationPaymentInline(admin.TabularInline):
    model = ObligationPayment
    extra = 0
    fields = ('payment_date', 'amount', 'principal_portion', 'interest_portion', 'reference_number')
    can_delete = False
    show_change_link = True
    max_num = 10


@admin.register(BankObligation)
class BankObligationAdmin(admin.ModelAdmin):
    list_display = ('obligation_number', 'obligation_type', 'bank', 'principal_amount', 
                   'interest_rate', 'payment_frequency', 'start_date', 'end_date', 
                   'remaining_balance', 'progress_percentage', 'is_active')
    list_filter = ('obligation_type', 'payment_frequency', 'is_active', 'bank')
    search_fields = ('obligation_number', 'bank__name', 'account_number', 'notes')
    readonly_fields = ('obligation_number', 'created_by', 'created_at', 'updated_at', 
                       'remaining_balance', 'progress_percentage', 'next_payment_date')
    date_hierarchy = 'start_date'
    fieldsets = (
        (None, {'fields': ('obligation_number', 'obligation_type', 'is_active')}),
        (_('Bank Details'), {'fields': ('bank', 'branch', 'account_number')}),
        (_('Financial Details'), {
            'fields': ('principal_amount', 'interest_rate', 'payment_frequency', 
                      'payment_amount', 'total_payments', 'remaining_balance', 
                      'progress_percentage')
        }),
        (_('Schedule'), {'fields': ('start_date', 'end_date', 'next_payment_date')}),
        (_('Additional Information'), {'fields': ('purpose', 'collateral', 'guarantors', 'notes')}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [ObligationPaymentInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ObligationPayment)
class ObligationPaymentAdmin(admin.ModelAdmin):
    list_display = ('obligation', 'payment_date', 'amount', 'principal_portion', 
                   'interest_portion', 'reference_number')
    list_filter = ('payment_date', 'obligation__obligation_type')
    search_fields = ('obligation__obligation_number', 'reference_number', 'notes')
    readonly_fields = ('created_by', 'created_at')
    date_hierarchy = 'payment_date'
    fieldsets = (
        (None, {'fields': ('obligation',)}),
        (_('Payment Details'), {
            'fields': ('payment_date', 'amount', 'principal_portion', 'interest_portion', 'reference_number')
        }),
        (_('Additional Information'), {'fields': ('notes',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at')}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
