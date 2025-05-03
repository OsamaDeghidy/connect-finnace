from rest_framework import serializers
from .models import Supplier, AccountPayable, PayableTransaction, PaymentReminder
from accounts_receivable.serializers import BankSerializer


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for the Supplier model."""
    
    total_outstanding = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'total_outstanding')


class PayableTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the PayableTransaction model."""
    
    class Meta:
        model = PayableTransaction
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')


class PaymentReminderSerializer(serializers.ModelSerializer):
    """Serializer for the PaymentReminder model."""
    
    class Meta:
        model = PaymentReminder
        fields = '__all__'
        read_only_fields = ('sent_by', 'sent_date')


class AccountPayableSerializer(serializers.ModelSerializer):
    """Serializer for the AccountPayable model."""
    
    bank_name = serializers.StringRelatedField(source='bank.name', read_only=True)
    supplier_name = serializers.StringRelatedField(source='supplier.name', read_only=True)
    transactions = PayableTransactionSerializer(many=True, read_only=True)
    reminders = PaymentReminderSerializer(many=True, read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AccountPayable
        fields = '__all__'
        read_only_fields = ('payment_number', 'created_by', 'created_at', 'updated_at', 
                           'last_reminder_date', 'days_until_due')
    
    def validate(self, data):
        """
        Validate that the due date is after the transaction date.
        """
        if data.get('due_date') and data.get('transaction_date') and data['due_date'] <= data['transaction_date']:
            raise serializers.ValidationError("Due date must be after transaction date.")
        return data


class SendReminderSerializer(serializers.Serializer):
    """Serializer for sending a payment reminder."""
    
    notes = serializers.CharField(required=False, allow_blank=True)


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for the dashboard summary data."""
    
    total_payables = serializers.DecimalField(max_digits=14, decimal_places=2)
    scheduled_payables = serializers.DecimalField(max_digits=14, decimal_places=2)
    in_process_payables = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_payables = serializers.DecimalField(max_digits=14, decimal_places=2)
    delayed_payables = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_suppliers = serializers.IntegerField()
    upcoming_reminders = PaymentReminderSerializer(many=True)
    recent_transactions = PayableTransactionSerializer(many=True)


class PayablesReportSerializer(serializers.Serializer):
    """Serializer for the payables report data."""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField(required=False)
    supplier = serializers.IntegerField(required=False)
    bank = serializers.IntegerField(required=False)


class UpcomingPaymentsSerializer(serializers.Serializer):
    """Serializer for the upcoming payments data."""
    
    days = serializers.IntegerField(default=30)  # Number of days to look ahead
