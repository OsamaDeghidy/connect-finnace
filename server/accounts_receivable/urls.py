from django.urls import path
from . import views

urlpatterns = [
    # Bank endpoints
    path('banks/', views.BankListCreateView.as_view(), name='bank-list-create'),
    path('banks/<int:pk>/', views.BankRetrieveUpdateDestroyView.as_view(), name='bank-detail'),
    
    # Client endpoints
    path('clients/', views.ClientListCreateView.as_view(), name='client-list-create'),
    path('clients/<int:pk>/', views.ClientRetrieveUpdateDestroyView.as_view(), name='client-detail'),
    
    # Account Receivable endpoints
    path('receivables/', views.AccountReceivableListCreateView.as_view(), name='receivable-list-create'),
    path('receivables/<int:pk>/', views.AccountReceivableRetrieveUpdateDestroyView.as_view(), name='receivable-detail'),
    path('receivables/<int:receivable_id>/transactions/', views.ReceivableTransactionListCreateView.as_view(), name='receivable-transaction-list-create'),
    path('receivables/transactions/<int:pk>/', views.ReceivableTransactionRetrieveUpdateDestroyView.as_view(), name='receivable-transaction-detail'),
    
    # Dashboard and reporting endpoints
    path('dashboard/summary/', views.DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('reports/receivables/', views.ReceivablesReportView.as_view(), name='receivables-report'),
]
