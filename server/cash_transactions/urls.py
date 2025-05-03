from django.urls import path
from . import views

urlpatterns = [
    # Transaction Category endpoints
    path('categories/', views.TransactionCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.TransactionCategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    
    # Cash Transaction endpoints
    path('transactions/', views.CashTransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/', views.CashTransactionRetrieveUpdateDestroyView.as_view(), name='transaction-detail'),
    
    # Cash Account endpoints
    path('accounts/', views.CashAccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<int:pk>/', views.CashAccountRetrieveUpdateDestroyView.as_view(), name='account-detail'),
    path('accounts/<int:account_id>/transactions/', views.CashAccountTransactionListCreateView.as_view(), name='account-transaction-list-create'),
    path('accounts/transactions/<int:pk>/', views.CashAccountTransactionRetrieveUpdateDestroyView.as_view(), name='account-transaction-detail'),
    
    # Dashboard and reporting endpoints
    path('dashboard/summary/', views.TransactionSummaryView.as_view(), name='transaction-summary'),
    path('reports/transactions/', views.TransactionReportView.as_view(), name='transaction-report'),
    path('reports/cash-flow/', views.CashFlowView.as_view(), name='cash-flow'),
]
