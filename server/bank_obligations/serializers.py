from rest_framework import serializers
from .models import BankObligation, ObligationPayment
from accounts_receivable.serializers import BankSerializer


class ObligationPaymentSerializer(serializers.ModelSerializer):
    """Serializer for the ObligationPayment model."""
    
    class Meta:
        model = ObligationPayment
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')


class BankObligationSerializer(serializers.ModelSerializer):
    """Serializer for the BankObligation model."""
    
    bank_name = serializers.StringRelatedField(source='bank.name', read_only=True)
    payments = ObligationPaymentSerializer(many=True, read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    next_payment_date = serializers.DateField(read_only=True)
    
    class Meta:
        model = BankObligation
        fields = '__all__'
        read_only_fields = ('obligation_number', 'created_by', 'created_at', 'updated_at',
                           'remaining_balance', 'progress_percentage', 'next_payment_date')
    
    def validate(self, data):
        """
        Validate that the end date is after the start date.
        """
        if data.get('end_date') and data.get('start_date') and data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data


class ObligationSummarySerializer(serializers.Serializer):
    """Serializer for the obligation summary data."""
    
    total_obligations = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_obligations_count = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.DecimalField(max_digits=14, decimal_places=2))
    by_bank = serializers.DictField(child=serializers.DecimalField(max_digits=14, decimal_places=2))
    upcoming_payments = serializers.ListField(child=serializers.DictField())


class ObligationReportSerializer(serializers.Serializer):
    """Serializer for the obligation report data."""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    obligation_type = serializers.CharField(required=False)
    bank = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)


class PaymentScheduleSerializer(serializers.Serializer):
    """Serializer for the payment schedule data."""
    
    obligation_id = serializers.IntegerField()
    months = serializers.IntegerField(default=12)  # Number of months to generate schedule for
