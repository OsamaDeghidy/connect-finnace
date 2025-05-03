from rest_framework import serializers
from .models import Bank, Client, AccountReceivable, ReceivableTransaction


class BankSerializer(serializers.ModelSerializer):
    """Serializer for the Bank model."""
    
    class Meta:
        model = Bank
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for the Client model."""
    
    total_outstanding = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'total_outstanding')


class ReceivableTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the ReceivableTransaction model."""
    
    class Meta:
        model = ReceivableTransaction
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')


class AccountReceivableSerializer(serializers.ModelSerializer):
    """Serializer for the AccountReceivable model."""
    
    bank_name = serializers.StringRelatedField(source='bank.name', read_only=True)
    client_name = serializers.StringRelatedField(source='client.name', read_only=True)
    transactions = ReceivableTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AccountReceivable
        fields = '__all__'
        read_only_fields = ('receipt_number', 'created_by', 'created_at', 'updated_at')
    
    def validate(self, data):
        """
        Validate that the due date is after the transaction date.
        """
        if data.get('due_date') and data.get('transaction_date') and data['due_date'] <= data['transaction_date']:
            raise serializers.ValidationError("Due date must be after transaction date.")
        return data


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for the dashboard summary data."""
    
    total_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    completed_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_clients = serializers.IntegerField()
    recent_transactions = ReceivableTransactionSerializer(many=True)


class ReceivablesReportSerializer(serializers.Serializer):
    """Serializer for the receivables report data."""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField(required=False)
    client = serializers.IntegerField(required=False)
    bank = serializers.IntegerField(required=False)
