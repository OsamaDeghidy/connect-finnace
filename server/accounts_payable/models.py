from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
from django.conf import settings
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver


class Supplier(models.Model):
    """Model for suppliers in the accounts payable system."""
    
    name = models.CharField(_('supplier name'), max_length=200)
    arabic_name = models.CharField(_('supplier name (Arabic)'), max_length=200, blank=True)
    contact_person = models.CharField(_('contact person'), max_length=100, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )
    phone = models.CharField(_('phone'), validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(_('email'), blank=True)
    address = models.TextField(_('address'), blank=True)
    tax_number = models.CharField(_('tax number'), max_length=50, blank=True)
    payment_terms = models.PositiveIntegerField(_('payment terms (days)'), default=60)
    pdf_file = models.FileField(_('PDF file'), upload_to='suppliers/pdf/', blank=True, null=True)
    is_active = models.BooleanField(_('active'), default=True)
    notes = models.TextField(_('notes'), blank=True, max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_suppliers'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_outstanding(self):
        """Calculate total outstanding amount for this supplier."""
        return self.payables.filter(status__in=['scheduled', 'in_process']).aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class AccountPayable(models.Model):
    """Model for accounts payable transactions."""
    
    STATUS_CHOICES = (
        ('covered', _('Covered')),
        ('under_coverage', _('Under Coverage')),
        ('delivered', _('Delivered')),
        ('covered_and_delivered', _('Covered and Delivered')),
        ('under_coverage_and_delivered', _('Under Coverage and Delivered')),
        ('disbursed', _('Disbursed')),
        ('covered_and_disbursed', _('Covered and Disbursed')),
        ('under_coverage_and_disbursed', _('Under Coverage and Disbursed')),
        ('rejected', _('Rejected')),
        ('returned', _('Returned')),
    )
    
    # Auto-generate payment number
    def generate_payment_number():
        today = datetime.date.today()
        year = today.year
        last_payment = AccountPayable.objects.filter(
            created_at__year=year
        ).order_by('-payment_number').first()
        
        if last_payment and last_payment.payment_number:
            try:
                # Extract the numeric part of the payment number
                last_number = int(last_payment.payment_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"AP-{year}-{new_number:05d}"
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='payables',
        verbose_name=_('supplier')
    )
    bank = models.ForeignKey(
        'accounts_receivable.Bank',  # Reference the Bank model from accounts_receivable
        on_delete=models.PROTECT,
        related_name='payables',
        verbose_name=_('bank')
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
    payment_number = models.CharField(
        _('payment number'),
        max_length=20,
        default=generate_payment_number,
        unique=True,
        editable=False
    )
    invoice_number = models.CharField(_('invoice number'), max_length=50, blank=True)
    invoice_date = models.DateField(_('invoice date'), null=True, blank=True)
    status = models.CharField(
        _('status'),
        max_length=40,
        choices=STATUS_CHOICES,
        default='covered'
    )
    notes = models.TextField(_('notes'), blank=True, max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payables'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_reminder_date = models.DateField(_('last reminder date'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('account payable')
        verbose_name_plural = _('accounts payable')
        ordering = ['-transaction_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gt=models.F('transaction_date')),
                name='ap_due_date_after_transaction_date'
            )
        ]
    
    def __str__(self):
        return f"{self.payment_number} - {self.supplier.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Check if due date is after transaction date
        if isinstance(self.due_date, str):
            self.due_date = datetime.datetime.strptime(self.due_date, '%Y-%m-%d').date()
        if isinstance(self.transaction_date, str):
            self.transaction_date = datetime.datetime.strptime(self.transaction_date, '%Y-%m-%d').date()
        if self.due_date and self.transaction_date and self.due_date <= self.transaction_date:
            raise ValueError(_('Due date must be after transaction date'))
        
        super().save(*args, **kwargs)
    
    def days_until_due(self):
        """Calculate days until due date."""
        if self.due_date:
            today = datetime.date.today()
            return (self.due_date - today).days
        return None


class PayableTransaction(models.Model):
    """Model to track transactions related to accounts payable."""
    
    TRANSACTION_TYPES = (
        ('partial_payment', _('Partial Payment')),
        ('full_payment', _('Full Payment')),
        ('adjustment', _('Adjustment')),
    )
    
    payable = models.ForeignKey(
        AccountPayable,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('payable')
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
        related_name='payable_transactions'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('payable transaction')
        verbose_name_plural = _('payable transactions')
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.payable.payment_number} - {self.transaction_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update payable status if full payment
        if self.transaction_type == 'full_payment':
            self.payable.status = 'paid'
            self.payable.save()


class PaymentReminder(models.Model):
    """Model to track payment reminders for accounts payable."""
    
    REMINDER_TYPES = (
        ('45_days', _('45 Days Before Due')),
        ('30_days', _('30 Days Before Due')),
        ('15_days', _('15 Days Before Due')),
        ('overdue', _('Overdue')),
    )
    
    payable = models.ForeignKey(
        AccountPayable,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('payable')
    )
    reminder_type = models.CharField(
        _('reminder type'),
        max_length=20,
        choices=REMINDER_TYPES
    )
    reminder_date = models.DateField(_('reminder date'))
    sent = models.BooleanField(_('sent'), default=False)
    sent_date = models.DateTimeField(_('sent date'), null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_reminders'
    )
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('payment reminder')
        verbose_name_plural = _('payment reminders')
        ordering = ['reminder_date']
        unique_together = ['payable', 'reminder_type']
    
    def __str__(self):
        return f"{self.payable.payment_number} - {self.get_reminder_type_display()}"


@receiver(post_save, sender=AccountPayable)
def create_payment_reminders(sender, instance, created, **kwargs):
    """Create payment reminders when a new AccountPayable is created."""
    if created and instance.due_date:
        # Calculate reminder dates
        due_date = instance.due_date
        reminder_dates = {
            '45_days': due_date - datetime.timedelta(days=45),
            '30_days': due_date - datetime.timedelta(days=30),
            '15_days': due_date - datetime.timedelta(days=15),
        }
        
        # Create reminder objects
        for reminder_type, reminder_date in reminder_dates.items():
            # Only create reminders for future dates
            if reminder_date >= datetime.date.today():
                PaymentReminder.objects.create(
                    payable=instance,
                    reminder_type=reminder_type,
                    reminder_date=reminder_date
                )
