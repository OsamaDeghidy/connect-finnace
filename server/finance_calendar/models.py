from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from accounts_receivable.models import AccountReceivable
from accounts_payable.models import AccountPayable
from bank_obligations.models import BankObligation
import datetime


class CalendarEvent(models.Model):
    """Model for calendar events that can be displayed in the calendar."""
    
    EVENT_TYPES = (
        ('receivable', _('Account Receivable')),
        ('payable', _('Account Payable')),
        ('obligation', _('Bank Obligation')),
        ('reminder', _('Payment Reminder')),
        ('custom', _('Custom Event')),
    )
    
    EVENT_COLORS = {
        'receivable': '#4CAF50',  # Green
        'payable': '#F44336',     # Red
        'obligation': '#2196F3',  # Blue
        'reminder': '#FF9800',    # Orange
        'custom': '#9C27B0',      # Purple
    }
    
    title = models.CharField(_('event title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    event_type = models.CharField(_('event type'), max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)
    all_day = models.BooleanField(_('all day event'), default=True)
    
    # Optional links to related models
    receivable = models.ForeignKey(
        AccountReceivable,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events'
    )
    payable = models.ForeignKey(
        AccountPayable,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events'
    )
    obligation = models.ForeignKey(
        BankObligation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events'
    )
    
    # Google Calendar integration
    google_calendar_id = models.CharField(_('Google Calendar ID'), max_length=255, blank=True)
    google_event_id = models.CharField(_('Google Event ID'), max_length=255, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('calendar event')
        verbose_name_plural = _('calendar events')
        ordering = ['start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def color(self):
        """Return the color for this event type."""
        return self.EVENT_COLORS.get(self.event_type, '#9C27B0')  # Default to purple
    
    @classmethod
    def sync_receivable_events(cls):
        """Sync events from accounts receivable."""
        # Delete existing receivable events
        cls.objects.filter(event_type='receivable').delete()
        
        # Create events for all active receivables
        for receivable in AccountReceivable.objects.filter(status__in=['active', 'overdue']):
            cls.objects.create(
                title=f"Due: {receivable.client.name} - {receivable.amount}",
                description=f"Receivable due from {receivable.client.name}",
                event_type='receivable',
                start_date=receivable.due_date,
                all_day=True,
                receivable=receivable,
                created_by=receivable.created_by
            )
    
    @classmethod
    def sync_payable_events(cls):
        """Sync events from accounts payable."""
        # Delete existing payable events
        cls.objects.filter(event_type='payable').delete()
        
        # Create events for all scheduled payables
        for payable in AccountPayable.objects.filter(status__in=['scheduled', 'in_process']):
            cls.objects.create(
                title=f"Pay: {payable.supplier.name} - {payable.amount}",
                description=f"Payment due to {payable.supplier.name}",
                event_type='payable',
                start_date=payable.due_date,
                all_day=True,
                payable=payable,
                created_by=payable.created_by
            )
    
    @classmethod
    def sync_obligation_events(cls):
        """Sync events from bank obligations."""
        # Delete existing obligation events
        cls.objects.filter(event_type='obligation').delete()
        
        # Create events for all active obligations
        for obligation in BankObligation.objects.all():
            # Create an event for the end date
            cls.objects.create(
                title=f"Obligation: {obligation.bank.name} - {obligation.principal_amount}",
                description=f"Bank obligation with {obligation.bank.name}",
                event_type='obligation',
                start_date=obligation.end_date,
                all_day=True,
                obligation=obligation
            )
    
    @classmethod
    def sync_all_events(cls):
        """Sync all events from all sources."""
        cls.sync_receivable_events()
        cls.sync_payable_events()
        cls.sync_obligation_events()
