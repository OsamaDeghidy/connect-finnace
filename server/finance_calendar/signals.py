from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts_receivable.models import AccountReceivable
from accounts_payable.models import AccountPayable, PaymentReminder
from bank_obligations.models import BankObligation
from .models import CalendarEvent


@receiver(post_save, sender=AccountReceivable)
def create_receivable_event(sender, instance, created, **kwargs):
    """Create or update calendar event when a receivable is created or updated."""
    if instance.status in ['active', 'overdue']:
        # Check if event already exists
        event = CalendarEvent.objects.filter(
            event_type='receivable',
            receivable=instance
        ).first()
        
        if event:
            # Update existing event
            event.title = f"Due: {instance.client.name} - {instance.amount}"
            event.start_date = instance.due_date
            event.save()
        else:
            # Create new event
            CalendarEvent.objects.create(
                title=f"Due: {instance.client.name} - {instance.amount}",
                description=f"Receivable due from {instance.client.name}",
                event_type='receivable',
                start_date=instance.due_date,
                all_day=True,
                receivable=instance,
                created_by=instance.created_by
            )


@receiver(post_save, sender=AccountPayable)
def create_payable_event(sender, instance, created, **kwargs):
    """Create or update calendar event when a payable is created or updated."""
    if instance.status in ['scheduled', 'in_process']:
        # Check if event already exists
        event = CalendarEvent.objects.filter(
            event_type='payable',
            payable=instance
        ).first()
        
        if event:
            # Update existing event
            event.title = f"Pay: {instance.supplier.name} - {instance.amount}"
            event.start_date = instance.due_date
            event.save()
        else:
            # Create new event
            CalendarEvent.objects.create(
                title=f"Pay: {instance.supplier.name} - {instance.amount}",
                description=f"Payment due to {instance.supplier.name}",
                event_type='payable',
                start_date=instance.due_date,
                all_day=True,
                payable=instance,
                created_by=instance.created_by
            )


@receiver(post_save, sender=BankObligation)
def create_obligation_event(sender, instance, created, **kwargs):
    """Create or update calendar event when an obligation is created or updated."""
    # Check if event already exists
    event = CalendarEvent.objects.filter(
        event_type='obligation',
        obligation=instance
    ).first()
    
    if event:
        # Update existing event
        event.title = f"Obligation: {instance.bank.name} - {instance.principal_amount}"
        event.start_date = instance.end_date
        event.save()
    else:
        # Create new event
        CalendarEvent.objects.create(
            title=f"Obligation: {instance.bank.name} - {instance.principal_amount}",
            description=f"Bank obligation with {instance.bank.name}",
            event_type='obligation',
            start_date=instance.end_date,
            all_day=True,
            obligation=instance
        )


@receiver(post_save, sender=PaymentReminder)
def create_reminder_event(sender, instance, created, **kwargs):
    """Create or update calendar event when a payment reminder is created or updated."""
    # Check if event already exists
    event = CalendarEvent.objects.filter(
        event_type='reminder',
        description__contains=f"Reminder ID: {instance.id}"
    ).first()
    
    if event:
        # Update existing event
        event.start_date = instance.reminder_date
        event.save()
    else:
        # Create new event
        supplier_name = instance.payable.supplier.name if instance.payable else "Unknown"
        CalendarEvent.objects.create(
            title=f"Reminder: {supplier_name}",
            description=f"Payment reminder for {supplier_name}. Reminder ID: {instance.id}",
            event_type='reminder',
            start_date=instance.reminder_date,
            all_day=True
        )


@receiver(post_delete, sender=AccountReceivable)
def delete_receivable_event(sender, instance, **kwargs):
    """Delete calendar event when a receivable is deleted."""
    CalendarEvent.objects.filter(
        event_type='receivable',
        receivable=instance
    ).delete()


@receiver(post_delete, sender=AccountPayable)
def delete_payable_event(sender, instance, **kwargs):
    """Delete calendar event when a payable is deleted."""
    CalendarEvent.objects.filter(
        event_type='payable',
        payable=instance
    ).delete()


@receiver(post_delete, sender=BankObligation)
def delete_obligation_event(sender, instance, **kwargs):
    """Delete calendar event when an obligation is deleted."""
    CalendarEvent.objects.filter(
        event_type='obligation',
        obligation=instance
    ).delete()


@receiver(post_delete, sender=PaymentReminder)
def delete_reminder_event(sender, instance, **kwargs):
    """Delete calendar event when a payment reminder is deleted."""
    CalendarEvent.objects.filter(
        event_type='reminder',
        description__contains=f"Reminder ID: {instance.id}"
    ).delete()
