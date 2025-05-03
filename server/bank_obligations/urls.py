from django.urls import path
from . import views

urlpatterns = [
    # Bank Obligation endpoints
    path('obligations/', views.BankObligationListCreateView.as_view(), name='obligation-list-create'),
    path('obligations/<int:pk>/', views.BankObligationRetrieveUpdateDestroyView.as_view(), name='obligation-detail'),
    
    # Obligation Payment endpoints
    path('obligations/<int:obligation_id>/payments/', views.ObligationPaymentListCreateView.as_view(), name='obligation-payment-list-create'),
    path('obligations/payments/<int:pk>/', views.ObligationPaymentRetrieveUpdateDestroyView.as_view(), name='obligation-payment-detail'),
    
    # Dashboard and reporting endpoints
    path('dashboard/summary/', views.ObligationSummaryView.as_view(), name='obligation-summary'),
    path('reports/obligations/', views.ObligationReportView.as_view(), name='obligation-report'),
    path('payment-schedule/', views.PaymentScheduleView.as_view(), name='payment-schedule'),
]
