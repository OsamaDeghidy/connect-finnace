from rest_framework import serializers
from .models import TransactionCategory, CashTransaction, CashAccount, CashAccountTransaction


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for the TransactionCategory model."""
    
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionCategory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_subcategories(self, obj):
        """Get all subcategories for this category."""
        subcategories = TransactionCategory.objects.filter(parent=obj)
        return TransactionCategorySerializer(subcategories, many=True).data


class CashTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the CashTransaction model."""
    
    category_name = serializers.StringRelatedField(source='category.name', read_only=True)
    created_by_name = serializers.StringRelatedField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CashTransaction
        fields = '__all__'
        read_only_fields = ('reference_number', 'created_by', 'created_at', 'updated_at')
    
    def validate(self, data):
        """
        Validate that the category type matches the transaction type.
        """
        category = data.get('category')
        transaction_type = data.get('transaction_type')
        
        if category and transaction_type and category.category_type != transaction_type:
            raise serializers.ValidationError("Category type must match transaction type.")
        return data


class CashAccountTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the CashAccountTransaction model."""
    
    transaction_details = CashTransactionSerializer(source='transaction', read_only=True)
    
    class Meta:
        model = CashAccountTransaction
        fields = '__all__'
        read_only_fields = ('created_at',)


class CashAccountSerializer(serializers.ModelSerializer):
    """Serializer for the CashAccount model."""
    
    current_balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    account_transactions = CashAccountTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = CashAccount
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'current_balance')


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for the transaction summary data."""
    
    total_income = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_cash_flow = serializers.DecimalField(max_digits=14, decimal_places=2)
    income_by_category = serializers.DictField(child=serializers.DecimalField(max_digits=14, decimal_places=2))
    expenses_by_category = serializers.DictField(child=serializers.DecimalField(max_digits=14, decimal_places=2))
    recent_transactions = CashTransactionSerializer(many=True)


class TransactionReportSerializer(serializers.Serializer):
    """Serializer for the transaction report data."""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    transaction_type = serializers.CharField(required=False)
    category = serializers.IntegerField(required=False)
    account = serializers.IntegerField(required=False)


class CashFlowSerializer(serializers.Serializer):
    """Serializer for the cash flow data."""
    
    period = serializers.CharField()  # 'daily', 'weekly', 'monthly', 'yearly'
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    account = serializers.IntegerField(required=False)
