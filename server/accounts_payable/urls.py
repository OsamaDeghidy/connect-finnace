from django.urls import path
from . import views

urlpatterns = [
    # Supplier endpoints
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierRetrieveUpdateDestroyView.as_view(), name='supplier-detail'),
    
    # Account Payable endpoints
    path('payables/', views.AccountPayableListCreateView.as_view(), name='payable-list-create'),
    path('payables/<int:pk>/', views.AccountPayableRetrieveUpdateDestroyView.as_view(), name='payable-detail'),
    path('payables/<int:payable_id>/transactions/', views.PayableTransactionListCreateView.as_view(), name='payable-transaction-list-create'),
    path('payables/transactions/<int:pk>/', views.PayableTransactionRetrieveUpdateDestroyView.as_view(), name='payable-transaction-detail'),
    
    # Payment Reminder endpoints
    path('reminders/', views.PaymentReminderListView.as_view(), name='payment-reminder-list'),
    path('reminders/<int:pk>/', views.PaymentReminderRetrieveUpdateView.as_view(), name='payment-reminder-detail'),
    path('reminders/<int:pk>/send/', views.SendReminderView.as_view(), name='send-reminder'),
    
    # Dashboard and reporting endpoints
    path('dashboard/summary/', views.DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('reports/payables/', views.PayablesReportView.as_view(), name='payables-report'),
    path('reports/upcoming-payments/', views.UpcomingPaymentsView.as_view(), name='upcoming-payments'),
]
