from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
import datetime


class TransactionCategory(models.Model):
    """Model for categorizing cash transactions."""
    
    CATEGORY_TYPES = (
        ('income', _('Income')),
        ('expense', _('Expense')),
    )
    
    name = models.CharField(_('category name'), max_length=100)
    arabic_name = models.CharField(_('category name (Arabic)'), max_length=100)
    category_type = models.CharField(_('category type'), max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('parent category')
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('transaction category')
        verbose_name_plural = _('transaction categories')
        ordering = ['category_type', 'name']
        unique_together = ['name', 'category_type', 'parent']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Return the full category path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class CashTransaction(models.Model):
    """Model for cash transactions (income and expenses)."""
    
    TRANSACTION_TYPES = (
        ('income', _('Income')),
        ('expense', _('Expense')),
    )
    
    # Auto-generate reference number
    def generate_reference_number():
        today = datetime.date.today()
        year = today.year
        last_transaction = CashTransaction.objects.filter(
            created_at__year=year
        ).order_by('-reference_number').first()
        
        if last_transaction and last_transaction.reference_number:
            try:
                # Extract the numeric part of the reference number
                last_number = int(last_transaction.reference_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"CT-{year}-{new_number:05d}"
    
    transaction_type = models.CharField(
        _('transaction type'),
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('category')
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    transaction_date = models.DateField(_('transaction date'), default=datetime.date.today)
    reference_number = models.CharField(
        _('reference number'),
        max_length=20,
        default=generate_reference_number,
        unique=True,
        editable=False
    )
    description = models.TextField(_('description'), blank=True)
    receipt_image = models.ImageField(_('receipt image'), upload_to='receipts/', blank=True, null=True)
    related_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_transactions',
        verbose_name=_('related transaction')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_transactions'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('cash transaction')
        verbose_name_plural = _('cash transactions')
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.reference_number} - {self.get_transaction_type_display()} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Ensure category type matches transaction type
        if self.category and self.category.category_type != self.transaction_type:
            raise ValueError(_('Category type must match transaction type'))
        
        super().save(*args, **kwargs)


class CashAccount(models.Model):
    """Model for cash accounts (e.g., petty cash, cash register)."""
    
    name = models.CharField(_('account name'), max_length=100)
    arabic_name = models.CharField(_('account name (Arabic)'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    initial_balance = models.DecimalField(
        _('initial balance'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('cash account')
        verbose_name_plural = _('cash accounts')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def current_balance(self):
        """Calculate the current balance of the account."""
        # Get all transactions for this account
        account_transactions = self.account_transactions.all()
        
        # Calculate total income and expenses
        income = account_transactions.filter(transaction__transaction_type='income').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        expense = account_transactions.filter(transaction__transaction_type='expense').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Calculate current balance
        return self.initial_balance + income - expense


class CashAccountTransaction(models.Model):
    """Model to link cash transactions to specific cash accounts."""
    
    account = models.ForeignKey(
        CashAccount,
        on_delete=models.CASCADE,
        related_name='account_transactions',
        verbose_name=_('cash account')
    )
    transaction = models.ForeignKey(
        CashTransaction,
        on_delete=models.CASCADE,
        related_name='account_transactions',
        verbose_name=_('transaction')
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('cash account transaction')
        verbose_name_plural = _('cash account transactions')
        ordering = ['-created_at']
        unique_together = ['account', 'transaction']
    
    def __str__(self):
        return f"{self.account.name} - {self.transaction.reference_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Ensure amount doesn't exceed transaction amount
        if self.amount > self.transaction.amount:
            raise ValueError(_('Amount cannot exceed transaction amount'))
        
        super().save(*args, **kwargs)
