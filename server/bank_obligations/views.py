from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils import timezone
import datetime
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import BankObligation, ObligationPayment
from .serializers import (
    BankObligationSerializer, ObligationPaymentSerializer,
    ObligationSummarySerializer, ObligationReportSerializer,
    PaymentScheduleSerializer
)


# Bank Obligation views
class BankObligationListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of bank obligations or create new bank obligation."""
    queryset = BankObligation.objects.all()
    serializer_class = BankObligationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['obligation_type', 'bank', 'is_active']
    search_fields = ['obligation_number', 'bank__name', 'purpose', 'notes']
    ordering_fields = ['start_date', 'end_date', 'principal_amount', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class BankObligationRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete bank obligation."""
    queryset = BankObligation.objects.all()
    serializer_class = BankObligationSerializer
    permission_classes = [permissions.IsAuthenticated]


# Obligation Payment views
class ObligationPaymentListCreateView(generics.ListCreateAPIView):
    """API view to retrieve list of payments for a specific obligation or create new payment."""
    serializer_class = ObligationPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        obligation_id = self.kwargs.get('obligation_id')
        return ObligationPayment.objects.filter(obligation_id=obligation_id)
    
    def perform_create(self, serializer):
        obligation_id = self.kwargs.get('obligation_id')
        obligation = BankObligation.objects.get(id=obligation_id)
        serializer.save(obligation=obligation, created_by=self.request.user)


class ObligationPaymentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete obligation payment."""
    queryset = ObligationPayment.objects.all()
    serializer_class = ObligationPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Dashboard and reporting views
class ObligationSummaryView(APIView):
    """API view to retrieve summary data for bank obligations dashboard."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get summary data
        total_obligations = BankObligation.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
        
        # Calculate total paid and remaining
        total_paid = ObligationPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_remaining = total_obligations - total_paid
        
        # Count active obligations
        active_obligations_count = BankObligation.objects.filter(is_active=True).count()
        
        # Group by type
        by_type = {}
        type_data = BankObligation.objects.values('obligation_type').annotate(
            total=Sum('principal_amount')
        )
        for item in type_data:
            by_type[item['obligation_type']] = item['total']
        
        # Group by bank
        by_bank = {}
        bank_data = BankObligation.objects.values('bank__name').annotate(
            total=Sum('principal_amount')
        )
        for item in bank_data:
            by_bank[item['bank__name']] = item['total']
        
        # Get upcoming payments
        today = timezone.now().date()
        next_month = today + datetime.timedelta(days=30)
        
        # This is a simplified approach - in a real application, you would calculate
        # the actual next payment dates based on payment frequency and last payment
        active_obligations = BankObligation.objects.filter(
            is_active=True,
            start_date__lte=next_month,
            end_date__gte=today
        )
        
        upcoming_payments = []
        for obligation in active_obligations:
            next_payment_date = obligation.next_payment_date
            if next_payment_date and next_payment_date <= next_month:
                upcoming_payments.append({
                    'id': obligation.id,
                    'obligation_number': obligation.obligation_number,
                    'bank': obligation.bank.name,
                    'payment_date': next_payment_date,
                    'amount': obligation.payment_amount,
                    'days_away': (next_payment_date - today).days
                })
        
        # Sort by payment date
        upcoming_payments.sort(key=lambda x: x['payment_date'])
        
        # Prepare data for serializer
        data = {
            'total_obligations': total_obligations,
            'total_remaining': total_remaining,
            'total_paid': total_paid,
            'active_obligations_count': active_obligations_count,
            'by_type': by_type,
            'by_bank': by_bank,
            'upcoming_payments': upcoming_payments
        }
        
        serializer = ObligationSummarySerializer(data)
        return Response(serializer.data)


class ObligationReportView(APIView):
    """API view to generate reports for bank obligations."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ObligationReportSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            obligation_type = serializer.validated_data.get('obligation_type')
            bank = serializer.validated_data.get('bank')
            is_active = serializer.validated_data.get('is_active')
            
            # Base queryset
            queryset = BankObligation.objects.filter(
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Apply filters if provided
            if obligation_type:
                queryset = queryset.filter(obligation_type=obligation_type)
            if bank:
                queryset = queryset.filter(bank_id=bank)
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)
            
            # Calculate payments made during the period
            payments_in_period = ObligationPayment.objects.filter(
                obligation__in=queryset,
                payment_date__gte=start_date,
                payment_date__lte=end_date
            )
            
            total_paid_in_period = payments_in_period.aggregate(total=Sum('amount'))['total'] or 0
            
            # Generate report data
            report_data = {
                'total_count': queryset.count(),
                'total_principal': queryset.aggregate(total=Sum('principal_amount'))['total'] or 0,
                'total_paid_in_period': total_paid_in_period,
                'by_type': queryset.values('obligation_type').annotate(
                    count=Count('id'),
                    total=Sum('principal_amount')
                ),
                'by_bank': queryset.values('bank__name').annotate(
                    count=Count('id'),
                    total=Sum('principal_amount')
                ),
                'payments_by_month': payments_in_period.extra(
                    select={'month': "EXTRACT(MONTH FROM payment_date)", 
                            'year': "EXTRACT(YEAR FROM payment_date)"}
                ).values('month', 'year').annotate(
                    total=Sum('amount')
                ).order_by('year', 'month'),
                'obligations': BankObligationSerializer(queryset, many=True).data
            }
            
            return Response(report_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentScheduleView(APIView):
    """API view to generate payment schedule for a bank obligation."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentScheduleSerializer(data=request.data)
        if serializer.is_valid():
            obligation_id = serializer.validated_data['obligation_id']
            months = serializer.validated_data.get('months', 12)
            
            try:
                obligation = BankObligation.objects.get(id=obligation_id)
            except BankObligation.DoesNotExist:
                return Response(
                    {'detail': 'Bank obligation not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get existing payments
            existing_payments = ObligationPayment.objects.filter(
                obligation=obligation
            ).order_by('payment_date')
            
            # Calculate remaining balance
            remaining_balance = obligation.remaining_balance
            
            # Calculate next payment date
            today = timezone.now().date()
            next_payment_date = obligation.next_payment_date or today
            
            # Generate payment schedule
            schedule = []
            current_date = next_payment_date
            current_balance = remaining_balance
            
            for i in range(months):
                # Skip if we've reached the end date or balance is zero
                if current_date > obligation.end_date or current_balance <= 0:
                    break
                
                # Calculate interest for this payment
                monthly_interest_rate = obligation.interest_rate / 100 / 12
                interest_amount = current_balance * monthly_interest_rate
                
                # Calculate principal portion
                principal_portion = min(obligation.payment_amount - interest_amount, current_balance)
                
                # Add to schedule
                schedule.append({
                    'payment_number': i + 1,
                    'payment_date': current_date,
                    'payment_amount': obligation.payment_amount,
                    'principal_portion': principal_portion,
                    'interest_portion': interest_amount,
                    'remaining_balance': current_balance - principal_portion
                })
                
                # Update balance and date for next iteration
                current_balance -= principal_portion
                
                # Calculate next payment date based on frequency
                if obligation.payment_frequency == 'monthly':
                    # Handle month overflow
                    year = current_date.year + (current_date.month + 1 - 1) // 12
                    month = (current_date.month + 1 - 1) % 12 + 1
                    day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                    current_date = datetime.date(year, month, day)
                elif obligation.payment_frequency == 'quarterly':
                    # Handle month overflow
                    year = current_date.year + (current_date.month + 3 - 1) // 12
                    month = (current_date.month + 3 - 1) % 12 + 1
                    day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                    current_date = datetime.date(year, month, day)
                elif obligation.payment_frequency == 'semi_annually':
                    # Handle month overflow
                    year = current_date.year + (current_date.month + 6 - 1) // 12
                    month = (current_date.month + 6 - 1) % 12 + 1
                    day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                    current_date = datetime.date(year, month, day)
                elif obligation.payment_frequency == 'annually':
                    # Handle leap year
                    year = current_date.year + 1
                    month = current_date.month
                    day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                    current_date = datetime.date(year, month, day)
                else:  # lump_sum
                    current_date = obligation.end_date
            
            # Prepare response data
            response_data = {
                'obligation': BankObligationSerializer(obligation).data,
                'existing_payments': ObligationPaymentSerializer(existing_payments, many=True).data,
                'remaining_balance': remaining_balance,
                'payment_schedule': schedule
            }
            
            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
