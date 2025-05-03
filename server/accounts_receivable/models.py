from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
from django.conf import settings
import datetime
from datetime import date


class Bank(models.Model):
    """Model for banks that can be used in transactions."""
    
    name = models.CharField(_('bank name'), max_length=100)
    arabic_name = models.CharField(_('bank name (Arabic)'), max_length=100)
    branch = models.CharField(_('branch'), max_length=100, blank=True)
    swift_code = models.CharField(_('SWIFT code'), max_length=20, blank=True)
    contact_person = models.CharField(_('contact person'), max_length=100, blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    address = models.TextField(_('address'), blank=True)
    pdf_file = models.FileField(_('PDF file'), upload_to='banks/pdf/', blank=True, null=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('bank')
        verbose_name_plural = _('banks')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Client(models.Model):
    """Model for clients in the accounts receivable system."""
    
    name = models.CharField(_('client name'), max_length=200)
    arabic_name = models.CharField(_('client name (Arabic)'), max_length=200, blank=True)
    contact_person = models.CharField(_('contact person'), max_length=100, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )
    phone = models.CharField(_('phone'), validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(_('email'), blank=True)
    address = models.TextField(_('address'), blank=True)
    tax_number = models.CharField(_('tax number'), max_length=50, blank=True)
    credit_limit = models.DecimalField(_('credit limit'), max_digits=14, decimal_places=2, default=0)
    pdf_file = models.FileField(_('PDF file'), upload_to='clients/pdf/', blank=True, null=True)
    is_active = models.BooleanField(_('active'), default=True)
    notes = models.TextField(_('notes'), blank=True, max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('client')
        verbose_name_plural = _('clients')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_outstanding(self):
        """Calculate total outstanding amount for this client."""
        return self.receivables.filter(status__in=['active', 'overdue']).aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class AccountReceivable(models.Model):
    """Model for accounts receivable transactions."""
    
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('pending', _('Pending')),
        ('overdue', _('Overdue')),
        ('treasury', _('Treasury')),
        ('with_representative', _('With Representative')),
        ('in_collection', _('In Collection')),
        ('treasury_rejected', _('Treasury Rejected')),
        ('collected', _('Collected')),
        ('client_rejected', _('Client Rejected')),
    )
    
    @classmethod
    def get_status_choices(cls):
        """Return the list of available status choices."""
        return cls.STATUS_CHOICES
    
    # Auto-generate receipt number
    def generate_receipt_number():
        today = datetime.date.today()
        year = today.year
        last_receipt = AccountReceivable.objects.filter(
            created_at__year=year
        ).order_by('-receipt_number').first()
        
        if last_receipt and last_receipt.receipt_number:
            try:
                # Extract the numeric part of the receipt number
                last_number = int(last_receipt.receipt_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"AR-{year}-{new_number:05d}"
    
    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name='receivables',
        verbose_name=_('bank')
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='receivables',
        verbose_name=_('client')
    )
    transaction_date = models.DateField(_('transaction date'), default=datetime.date.today)
    due_date = models.DateField(_('due date'))
    amount = models.DecimalField(
        _('amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    check_number = models.CharField(_('check number'), max_length=50)
    receipt_number = models.CharField(
        _('receipt number'),
        max_length=20,
        default=generate_receipt_number,
        unique=True,
        editable=False
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    notes = models.TextField(_('notes'), blank=True, max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_receivables'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('account receivable')
        verbose_name_plural = _('accounts receivable')
        ordering = ['-transaction_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gt=models.F('transaction_date')),
                name='due_date_after_transaction_date'
            )
        ]
    
    def __str__(self):
        return f"{self.receipt_number} - {self.client.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Ensure both self.due_date and today are date objects
        if isinstance(self.due_date, str):
            self.due_date = datetime.datetime.strptime(self.due_date, '%Y-%m-%d').date()
        today = date.today()

        if self.status != 'completed' and self.due_date < today:
            raise ValueError('Due date cannot be in the past for incomplete receivables')
        super().save(*args, **kwargs)


class ReceivableTransaction(models.Model):
    """Model to track transactions related to accounts receivable."""
    
    TRANSACTION_TYPES = (
        ('deposit', _('Deposit')),
        ('partial_payment', _('Partial Payment')),
        ('full_payment', _('Full Payment')),
        ('return', _('Return')),
        ('adjustment', _('Adjustment')),
    )
    
    receivable = models.ForeignKey(
        AccountReceivable,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('receivable')
    )
    transaction_type = models.CharField(
        _('transaction type'),
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    transaction_date = models.DateField(_('transaction date'), default=datetime.date.today)
    reference = models.CharField(_('reference'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='receivable_transactions'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('receivable transaction')
        verbose_name_plural = _('receivable transactions')
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.receivable.receipt_number} - {self.transaction_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update receivable status if full payment
        if self.transaction_type == 'full_payment':
            self.receivable.status = 'completed'
            self.receivable.save()
