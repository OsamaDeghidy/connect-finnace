from django.db.models import Sum, Count
from django.utils import timezone
import datetime
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import Supplier, AccountPayable, PayableTransaction, PaymentReminder
from .serializers import (
    SupplierSerializer, AccountPayableSerializer, PayableTransactionSerializer,
    PaymentReminderSerializer, SendReminderSerializer, DashboardSummarySerializer,
    PayablesReportSerializer, UpcomingPaymentsSerializer
)


# Supplier views
class SupplierListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of suppliers or create new supplier."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'payment_terms']
    search_fields = ['name', 'arabic_name', 'phone', 'email', 'tax_number']
    ordering_fields = ['name', 'payment_terms', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SupplierRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete supplier."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]


# Account Payable views
class AccountPayableListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of account payables or create new account payable."""
    queryset = AccountPayable.objects.all()
    serializer_class = AccountPayableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'bank', 'supplier', 'transaction_date']
    search_fields = ['payment_number', 'check_number', 'supplier__name', 'invoice_number', 'notes']
    ordering_fields = ['transaction_date', 'due_date', 'amount', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AccountPayableRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete account payable."""
    queryset = AccountPayable.objects.all()
    serializer_class = AccountPayableSerializer
    permission_classes = [permissions.IsAuthenticated]


# Payable Transaction views
class PayableTransactionListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of transactions for a specific payable or create new transaction."""
    serializer_class = PayableTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        payable_id = self.kwargs.get('payable_id')
        return PayableTransaction.objects.filter(payable_id=payable_id)
    
    def perform_create(self, serializer):
        payable_id = self.kwargs.get('payable_id')
        payable = AccountPayable.objects.get(id=payable_id)
        serializer.save(payable=payable, created_by=self.request.user)


class PayableTransactionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete payable transaction."""
    queryset = PayableTransaction.objects.all()
    serializer_class = PayableTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


# Payment Reminder views
class PaymentReminderListView(generics.ListAPIView):
    """API view to retrieve list of payment reminders."""
    serializer_class = PaymentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reminder_type', 'sent', 'reminder_date']
    ordering_fields = ['reminder_date', 'payable__due_date']
    
    def get_queryset(self):
        return PaymentReminder.objects.all()


class PaymentReminderRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """API view to retrieve or update payment reminder."""
    queryset = PaymentReminder.objects.all()
    serializer_class = PaymentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]


class SendReminderView(APIView):
    """API view to send a payment reminder."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            reminder = PaymentReminder.objects.get(pk=pk)
        except PaymentReminder.DoesNotExist:
            return Response(
                {'detail': 'Payment reminder not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SendReminderSerializer(data=request.data)
        if serializer.is_valid():
            # Mark reminder as sent
            reminder.sent = True
            reminder.sent_date = timezone.now()
            reminder.sent_by = request.user
            if serializer.validated_data.get('notes'):
                reminder.notes = serializer.validated_data['notes']
            reminder.save()
            
            # Update last reminder date on the payable
            payable = reminder.payable
            payable.last_reminder_date = timezone.now().date()
            payable.save()
            
            # In a real application, you would send an email or notification here
            
            return Response(
                {'detail': 'Reminder sent successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Dashboard and reporting views
class DashboardSummaryView(APIView):
    """API view to retrieve summary data for dashboard."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get summary data
        total_payables = AccountPayable.objects.aggregate(total=Sum('amount'))['total'] or 0
        scheduled_payables = AccountPayable.objects.filter(status='scheduled').aggregate(total=Sum('amount'))['total'] or 0
        in_process_payables = AccountPayable.objects.filter(status='in_process').aggregate(total=Sum('amount'))['total'] or 0
        paid_payables = AccountPayable.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        delayed_payables = AccountPayable.objects.filter(status='delayed').aggregate(total=Sum('amount'))['total'] or 0
        total_suppliers = Supplier.objects.count()
        
        # Get upcoming reminders
        today = timezone.now().date()
        upcoming_reminders = PaymentReminder.objects.filter(
            sent=False,
            reminder_date__gte=today
        ).order_by('reminder_date')[:10]
        
        # Get recent transactions
        recent_transactions = PayableTransaction.objects.order_by('-created_at')[:10]
        
        # Prepare data for serializer
        data = {
            'total_payables': total_payables,
            'scheduled_payables': scheduled_payables,
            'in_process_payables': in_process_payables,
            'paid_payables': paid_payables,
            'delayed_payables': delayed_payables,
            'total_suppliers': total_suppliers,
            'upcoming_reminders': upcoming_reminders,
            'recent_transactions': recent_transactions
        }
        
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class PayablesReportView(APIView):
    """API view to generate reports for payables."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PayablesReportSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            status_filter = serializer.validated_data.get('status')
            supplier_filter = serializer.validated_data.get('supplier')
            bank_filter = serializer.validated_data.get('bank')
            
            # Base queryset
            queryset = AccountPayable.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            # Apply filters if provided
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if supplier_filter:
                queryset = queryset.filter(supplier_id=supplier_filter)
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
                'by_supplier': queryset.values('supplier__name').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'by_bank': queryset.values('bank__name').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'payables': AccountPayableSerializer(queryset, many=True).data
            }
            
            return Response(report_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpcomingPaymentsView(APIView):
    """API view to retrieve upcoming payments."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = UpcomingPaymentsSerializer(data=request.data)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            today = timezone.now().date()
            end_date = today + datetime.timedelta(days=days)
            
            # Get upcoming payments
            upcoming_payments = AccountPayable.objects.filter(
                status__in=['scheduled', 'in_process'],
                due_date__gte=today,
                due_date__lte=end_date
            ).order_by('due_date')
            
            # Prepare data
            data = {
                'upcoming_payments': AccountPayableSerializer(upcoming_payments, many=True).data,
                'total_amount': upcoming_payments.aggregate(total=Sum('amount'))['total'] or 0,
                'count': upcoming_payments.count()
            }
            
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
