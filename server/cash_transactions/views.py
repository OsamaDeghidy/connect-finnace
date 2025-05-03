from django.db.models import Sum, Count, Q
from django.utils import timezone
import datetime
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import TransactionCategory, CashTransaction, CashAccount, CashAccountTransaction
from .serializers import (
    TransactionCategorySerializer, CashTransactionSerializer,
    CashAccountSerializer, CashAccountTransactionSerializer,
    TransactionSummarySerializer, TransactionReportSerializer,
    CashFlowSerializer
)


# Transaction Category views
class TransactionCategoryListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of transaction categories or create new category."""
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_type', 'is_active', 'parent']
    search_fields = ['name', 'arabic_name', 'description']
    ordering_fields = ['name', 'category_type', 'created_at']
    
    def get_queryset(self):
        # Only return top-level categories (no parent) by default
        parent = self.request.query_params.get('parent', None)
        if parent is None and not any(key.startswith('parent') for key in self.request.query_params):
            return TransactionCategory.objects.filter(parent=None)
        return TransactionCategory.objects.all()


class TransactionCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete transaction category."""
    queryset = TransactionCategory.objects.all()
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# Cash Transaction views
class CashTransactionListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of cash transactions or create new transaction."""
    queryset = CashTransaction.objects.all()
    serializer_class = CashTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'category', 'transaction_date']
    search_fields = ['reference_number', 'description']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CashTransactionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete cash transaction."""
    queryset = CashTransaction.objects.all()
    serializer_class = CashTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


# Cash Account views
class CashAccountListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of cash accounts or create new account."""
    queryset = CashAccount.objects.all()
    serializer_class = CashAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'arabic_name', 'description']
    ordering_fields = ['name', 'created_at']


class CashAccountRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete cash account."""
    queryset = CashAccount.objects.all()
    serializer_class = CashAccountSerializer
    permission_classes = [permissions.IsAuthenticated]


# Cash Account Transaction views
class CashAccountTransactionListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of transactions for a specific account or create new transaction."""
    serializer_class = CashAccountTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return CashAccountTransaction.objects.filter(account_id=account_id)


class CashAccountTransactionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete cash account transaction."""
    queryset = CashAccountTransaction.objects.all()
    serializer_class = CashAccountTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


# Dashboard and reporting views
class TransactionSummaryView(APIView):
    """API view to retrieve summary data for cash transactions dashboard."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get query parameters for date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        # Default to current month if no dates provided
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = datetime.date(today.year, today.month, 1)
            # Get last day of current month
            if today.month == 12:
                end_date = datetime.date(today.year, 12, 31)
            else:
                end_date = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
        else:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Filter transactions by date range
        transactions = CashTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Calculate totals
        income_transactions = transactions.filter(transaction_type='income')
        expense_transactions = transactions.filter(transaction_type='expense')
        
        total_income = income_transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = expense_transactions.aggregate(total=Sum('amount'))['total'] or 0
        net_cash_flow = total_income - total_expenses
        
        # Group by category
        income_by_category = {}
        income_categories = income_transactions.values('category__name').annotate(
            total=Sum('amount')
        )
        for item in income_categories:
            income_by_category[item['category__name']] = item['total']
        
        expenses_by_category = {}
        expense_categories = expense_transactions.values('category__name').annotate(
            total=Sum('amount')
        )
        for item in expense_categories:
            expenses_by_category[item['category__name']] = item['total']
        
        # Get recent transactions
        recent_transactions = transactions.order_by('-transaction_date', '-created_at')[:10]
        
        # Prepare data for serializer
        data = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_cash_flow': net_cash_flow,
            'income_by_category': income_by_category,
            'expenses_by_category': expenses_by_category,
            'recent_transactions': recent_transactions
        }
        
        serializer = TransactionSummarySerializer(data)
        return Response(serializer.data)


class TransactionReportView(APIView):
    """API view to generate reports for cash transactions."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TransactionReportSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            transaction_type = serializer.validated_data.get('transaction_type')
            category = serializer.validated_data.get('category')
            account = serializer.validated_data.get('account')
            
            # Base queryset
            queryset = CashTransaction.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            # Apply filters if provided
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            if category:
                # Include subcategories
                category_ids = [category]
                subcategories = TransactionCategory.objects.filter(parent_id=category)
                category_ids.extend(subcategories.values_list('id', flat=True))
                queryset = queryset.filter(category_id__in=category_ids)
            if account:
                # Filter by account through CashAccountTransaction
                transaction_ids = CashAccountTransaction.objects.filter(
                    account_id=account
                ).values_list('transaction_id', flat=True)
                queryset = queryset.filter(id__in=transaction_ids)
            
            # Generate report data
            report_data = {
                'total_count': queryset.count(),
                'total_amount': queryset.aggregate(total=Sum('amount'))['total'] or 0,
                'by_type': queryset.values('transaction_type').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'by_category': queryset.values('category__name').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'by_date': queryset.extra(
                    select={'day': "EXTRACT(DAY FROM transaction_date)", 
                            'month': "EXTRACT(MONTH FROM transaction_date)",
                            'year': "EXTRACT(YEAR FROM transaction_date)"}
                ).values('day', 'month', 'year').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ).order_by('year', 'month', 'day'),
                'transactions': CashTransactionSerializer(queryset, many=True).data
            }
            
            return Response(report_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CashFlowView(APIView):
    """API view to generate cash flow data over time."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CashFlowSerializer(data=request.data)
        if serializer.is_valid():
            period = serializer.validated_data['period']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            account_id = serializer.validated_data.get('account')
            
            # Base queryset
            queryset = CashTransaction.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            # Filter by account if provided
            if account_id:
                transaction_ids = CashAccountTransaction.objects.filter(
                    account_id=account_id
                ).values_list('transaction_id', flat=True)
                queryset = queryset.filter(id__in=transaction_ids)
            
            # Group by period
            if period == 'daily':
                date_trunc = "transaction_date"
                date_format = "%Y-%m-%d"
            elif period == 'weekly':
                # This is a simplified approach - in a real application, you would use
                # database-specific functions to group by week
                date_trunc = "DATE_TRUNC('week', transaction_date)"
                date_format = "%Y-%m-%d"
            elif period == 'monthly':
                date_trunc = "EXTRACT(YEAR FROM transaction_date) || '-' || EXTRACT(MONTH FROM transaction_date)"
                date_format = "%Y-%m"
            else:  # yearly
                date_trunc = "EXTRACT(YEAR FROM transaction_date)"
                date_format = "%Y"
            
            # This is a simplified approach - in a real application, you would use
            # database-specific functions for more efficient grouping
            cash_flow_data = []
            current_date = start_date
            while current_date <= end_date:
                if period == 'daily':
                    period_start = current_date
                    period_end = current_date
                    current_date += datetime.timedelta(days=1)
                    period_label = period_start.strftime(date_format)
                elif period == 'weekly':
                    # Start on Monday
                    period_start = current_date - datetime.timedelta(days=current_date.weekday())
                    period_end = period_start + datetime.timedelta(days=6)
                    current_date = period_end + datetime.timedelta(days=1)
                    period_label = f"{period_start.strftime(date_format)} to {period_end.strftime(date_format)}"
                elif period == 'monthly':
                    period_start = datetime.date(current_date.year, current_date.month, 1)
                    # Get last day of month
                    if current_date.month == 12:
                        period_end = datetime.date(current_date.year, 12, 31)
                    else:
                        period_end = datetime.date(current_date.year, current_date.month + 1, 1) - datetime.timedelta(days=1)
                    # Move to first day of next month
                    if current_date.month == 12:
                        current_date = datetime.date(current_date.year + 1, 1, 1)
                    else:
                        current_date = datetime.date(current_date.year, current_date.month + 1, 1)
                    period_label = period_start.strftime(date_format)
                else:  # yearly
                    period_start = datetime.date(current_date.year, 1, 1)
                    period_end = datetime.date(current_date.year, 12, 31)
                    current_date = datetime.date(current_date.year + 1, 1, 1)
                    period_label = period_start.strftime(date_format)
                
                # Get transactions for this period
                period_transactions = queryset.filter(
                    transaction_date__gte=period_start,
                    transaction_date__lte=period_end
                )
                
                # Calculate income and expenses
                income = period_transactions.filter(transaction_type='income').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                expenses = period_transactions.filter(transaction_type='expense').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                # Add to cash flow data
                cash_flow_data.append({
                    'period': period_label,
                    'income': income,
                    'expenses': expenses,
                    'net': income - expenses
                })
                
                # Break if we've reached the end date
                if current_date > end_date:
                    break
            
            # Calculate cumulative cash flow
            cumulative = 0
            for item in cash_flow_data:
                cumulative += item['net']
                item['cumulative'] = cumulative
            
            return Response(cash_flow_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
