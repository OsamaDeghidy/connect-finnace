from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TransactionCategory, CashTransaction, CashAccount, CashAccountTransaction


class SubcategoryInline(admin.TabularInline):
    model = TransactionCategory
    extra = 0
    fields = ('name', 'arabic_name', 'is_active')
    fk_name = 'parent'
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'category_type', 'parent', 'full_path', 'is_active')
    list_filter = ('category_type', 'is_active', 'parent')
    search_fields = ('name', 'arabic_name', 'description')
    fieldsets = (
        (None, {'fields': ('name', 'arabic_name', 'category_type', 'is_active')}),
        (_('Hierarchy'), {'fields': ('parent',)}),
        (_('Additional Information'), {'fields': ('description',)}),
    )
    inlines = [SubcategoryInline]


class CashAccountTransactionInline(admin.TabularInline):
    model = CashAccountTransaction
    extra = 0
    fields = ('account', 'amount', 'notes')
    can_delete = False
    show_change_link = True
    max_num = 5


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'transaction_type', 'category', 'amount', 
                   'transaction_date', 'created_by')
    list_filter = ('transaction_type', 'transaction_date', 'category')
    search_fields = ('reference_number', 'description', 'category__name')
    readonly_fields = ('reference_number', 'created_by', 'created_at', 'updated_at')
    date_hierarchy = 'transaction_date'
    fieldsets = (
        (None, {'fields': ('reference_number', 'transaction_type', 'category')}),
        (_('Transaction Details'), {'fields': ('amount', 'transaction_date', 'description')}),
        (_('Attachments'), {'fields': ('receipt_image',)}),
        (_('Related Information'), {'fields': ('related_to',)}),
        (_('System Information'), {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [CashAccountTransactionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class AccountTransactionInline(admin.TabularInline):
    model = CashAccountTransaction
    extra = 0
    fields = ('transaction', 'amount', 'notes')
    can_delete = False
    show_change_link = True
    max_num = 10


@admin.register(CashAccount)
class CashAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'initial_balance', 'current_balance', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'arabic_name', 'description')
    readonly_fields = ('current_balance', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'arabic_name', 'is_active')}),
        (_('Financial Information'), {'fields': ('initial_balance', 'current_balance')}),
        (_('Additional Information'), {'fields': ('description',)}),
        (_('System Information'), {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [AccountTransactionInline]


@admin.register(CashAccountTransaction)
class CashAccountTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction', 'amount', 'created_at')
    list_filter = ('account', 'transaction__transaction_type', 'created_at')
    search_fields = ('account__name', 'transaction__reference_number', 'notes')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {'fields': ('account', 'transaction')}),
        (_('Transaction Details'), {'fields': ('amount', 'notes')}),
        (_('System Information'), {'fields': ('created_at',)}),
    )
