from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import datetime


class Bank(models.Model):
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class BankObligation(models.Model):
    """Model for bank obligations such as loans, credit lines, and letters of credit."""
    
    OBLIGATION_TYPES = (
        ('loan', _('Loan')),
        ('credit_line', _('Credit Line')),
        ('letter_of_credit', _('Letter of Credit')),
    )
    
    STATUS_CHOICES = (
        ('created', _('Created')),
        ('covered_with_papers', _('Covered with Papers')),
        ('covered_with_cash', _('Covered with Cash')),
        ('paid', _('Paid')),
    )
    
    PAYMENT_FREQUENCY = (
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('semi_annually', _('Semi-Annually')),
        ('annually', _('Annually')),
        ('lump_sum', _('Lump Sum')),
    )
    
    # Auto-generate obligation number
    def generate_obligation_number():
        today = datetime.date.today()
        year = today.year
        last_obligation = BankObligation.objects.filter(
            created_at__year=year
        ).order_by('-obligation_number').first()
        
        if last_obligation and last_obligation.obligation_number:
            try:
                # Extract the numeric part of the obligation number
                last_number = int(last_obligation.obligation_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"BO-{year}-{new_number:05d}"
    
    obligation_type = models.CharField(
        _('obligation type'),
        max_length=20,
        choices=OBLIGATION_TYPES
    )
    obligation_number = models.CharField(
        _('obligation number'),
        max_length=20,
        default=generate_obligation_number,
        unique=True,
        editable=False
    )
    bank = models.ForeignKey(
        'accounts_receivable.Bank',  # Reference the Bank model from accounts_receivable
        on_delete=models.PROTECT,
        related_name='obligations',
        verbose_name=_('bank')
    )
    branch = models.CharField(_('branch'), max_length=100, blank=True)
    account_number = models.CharField(_('account number'), max_length=50, blank=True)
    
    # Financial details
    principal_amount = models.DecimalField(
        _('principal amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    interest_rate = models.DecimalField(
        _('interest rate (%)'),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    payment_frequency = models.CharField(
        _('payment frequency'),
        max_length=20,
        choices=PAYMENT_FREQUENCY,
        default='monthly'
    )
    payment_amount = models.DecimalField(
        _('payment amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    total_payments = models.PositiveIntegerField(_('total number of payments'), default=1)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=30,
        choices=STATUS_CHOICES,
        default='created'
    )
    
    # Additional information
    purpose = models.TextField(_('purpose'), blank=True)
    collateral = models.TextField(_('collateral'), blank=True)
    guarantors = models.TextField(_('guarantors'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # System fields
    is_active = models.BooleanField(_('active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_obligations'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('bank obligation')
        verbose_name_plural = _('bank obligations')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.get_obligation_type_display()} - {self.bank.name} - {self.principal_amount}"
    
    def clean(self):
        # Validate end_date is after start_date
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('End date must be after start date.')
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def remaining_balance(self):
        """Calculate the remaining balance of the obligation."""
        paid_amount = self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return self.principal_amount - paid_amount
    
    @property
    def progress_percentage(self):
        """Calculate the percentage of the obligation that has been paid."""
        if self.principal_amount == 0:
            return 0
        paid_amount = self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return min(100, (paid_amount / self.principal_amount) * 100)
    
    @property
    def next_payment_date(self):
        """Calculate the next payment date based on the payment schedule."""
        today = datetime.date.today()
        
        # If obligation is completed or not started yet
        if not self.is_active or today < self.start_date:
            return None
        
        # If obligation has ended
        if today > self.end_date:
            return None
        
        # Get the last payment date
        last_payment = self.payments.order_by('-payment_date').first()
        
        if not last_payment:
            return self.start_date
        
        # Calculate next payment date based on frequency
        last_date = last_payment.payment_date
        
        def add_months(date, months):
            """Helper function to add months to a date while handling month/year overflow"""
            year = date.year + (date.month + months - 1) // 12
            month = (date.month + months - 1) % 12 + 1
            # Handle the case where the day might not exist in the target month
            day = min(date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                               31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            return datetime.date(year, month, day)
        
        if self.payment_frequency == 'monthly':
            next_date = add_months(last_date, 1)
        elif self.payment_frequency == 'quarterly':
            next_date = add_months(last_date, 3)
        elif self.payment_frequency == 'semi_annually':
            next_date = add_months(last_date, 6)
        elif self.payment_frequency == 'annually':
            next_date = add_months(last_date, 12)
        else:  # lump_sum
            next_date = self.end_date
        
        # If next payment date is after end date, return end date
        if next_date > self.end_date:
            return self.end_date
        
        return next_date


class ObligationPayment(models.Model):
    """Model to track payments made for bank obligations."""
    
    obligation = models.ForeignKey(
        BankObligation,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('obligation')
    )
    payment_date = models.DateField(_('payment date'))
    amount = models.DecimalField(
        _('amount'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    principal_portion = models.DecimalField(
        _('principal portion'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    interest_portion = models.DecimalField(
        _('interest portion'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reference_number = models.CharField(_('reference number'), max_length=50, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='obligation_payments'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('obligation payment')
        verbose_name_plural = _('obligation payments')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.obligation.obligation_number} - {self.payment_date} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Ensure principal + interest = amount
        if self.principal_portion + self.interest_portion != self.amount:
            raise ValueError(_('Principal portion plus interest portion must equal the total amount'))
        
        super().save(*args, **kwargs)
