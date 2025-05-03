from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import Bank, Client, AccountReceivable, ReceivableTransaction
from .serializers import (
    BankSerializer, ClientSerializer, AccountReceivableSerializer,
    ReceivableTransactionSerializer, DashboardSummarySerializer,
    ReceivablesReportSerializer
)


# Bank views
class BankListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of banks or create new bank."""
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'arabic_name', 'branch', 'swift_code']
    ordering_fields = ['name', 'created_at']


class BankRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete bank."""
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [permissions.IsAuthenticated]


# Client views
class ClientListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of clients or create new client."""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'arabic_name', 'phone', 'email', 'tax_number']
    ordering_fields = ['name', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ClientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete client."""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]


# Account Receivable views
class AccountReceivableListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of account receivables or create new account receivable."""
    queryset = AccountReceivable.objects.all()
    serializer_class = AccountReceivableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'bank', 'client', 'transaction_date']
    search_fields = ['receipt_number', 'check_number', 'client__name', 'notes']
    ordering_fields = ['transaction_date', 'due_date', 'amount', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AccountReceivableRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete account receivable."""
    queryset = AccountReceivable.objects.all()
    serializer_class = AccountReceivableSerializer
    permission_classes = [permissions.IsAuthenticated]


# Receivable Transaction views
class ReceivableTransactionListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of transactions for a specific receivable or create new transaction."""
    serializer_class = ReceivableTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        receivable_id = self.kwargs.get('receivable_id')
        return ReceivableTransaction.objects.filter(receivable_id=receivable_id)
    
    def perform_create(self, serializer):
        receivable_id = self.kwargs.get('receivable_id')
        receivable = AccountReceivable.objects.get(id=receivable_id)
        serializer.save(receivable=receivable, created_by=self.request.user)


class ReceivableTransactionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete receivable transaction."""
    queryset = ReceivableTransaction.objects.all()
    serializer_class = ReceivableTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


# Dashboard and reporting views
class DashboardSummaryView(APIView):
    """API view to retrieve summary data for dashboard."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get summary data
        total_receivables = AccountReceivable.objects.aggregate(total=Sum('amount'))['total'] or 0
        active_receivables = AccountReceivable.objects.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
        completed_receivables = AccountReceivable.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        overdue_receivables = AccountReceivable.objects.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0
        pending_receivables = AccountReceivable.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
        total_clients = Client.objects.count()
        
        # Get recent transactions
        recent_transactions = ReceivableTransaction.objects.order_by('-created_at')[:10]
        
        # Prepare data for serializer
        data = {
            'total_receivables': total_receivables,
            'active_receivables': active_receivables,
            'completed_receivables': completed_receivables,
            'overdue_receivables': overdue_receivables,
            'pending_receivables': pending_receivables,
            'total_clients': total_clients,
            'recent_transactions': recent_transactions
        }
        
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class ReceivablesReportView(APIView):
    """API view to generate reports for receivables."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ReceivablesReportSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            status_filter = serializer.validated_data.get('status')
            client_filter = serializer.validated_data.get('client')
            bank_filter = serializer.validated_data.get('bank')
            
            # Base queryset
            queryset = AccountReceivable.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            # Apply filters if provided
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if client_filter:
                queryset = queryset.filter(client_id=client_filter)
            if bank_filter:
                queryset = queryset.filter(bank_id=bank_filter)
            
            # Generate report data
            report_data = {
                'total_count': queryset.count(),
                'total_amount': queryset.aggregate(total=Sum('amount'))['total'] or 0,
                'by_status': queryset.values('status').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'by_client': queryset.values('client__name').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'by_bank': queryset.values('bank__name').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'receivables': AccountReceivableSerializer(queryset, many=True).data
            }
            
            return Response(report_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
