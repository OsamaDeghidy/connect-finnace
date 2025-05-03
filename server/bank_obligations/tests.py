from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts_receivable.models import Bank
from .models import BankObligation

class BankObligationsAPITestCase(APITestCase):
    def setUp(self):
        self.obligations_url = '/api/v1/bank-obligations/obligations/'
        self.login_url = '/api/v1/accounts/token/'
        self.user_data = {'email': 'testuser@example.com', 'password': 'testpassword'}

        # Create a test user and get JWT token
        User = get_user_model()
        self.user = User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.token = response.data['access']

        # Add sample data
        for i in range(3):
            bank = Bank.objects.create(
                name=f"Bank {i+1}",
                branch=f"Branch {i+1}",
                swift_code=f"SWIFT{i+1}",
                contact_person=f"Contact {i+1}",
                phone=f"+966500000{i+1}",
                email=f"bank{i+1}@example.com",
                address=f"Address {i+1}"
            )
            BankObligation.objects.create(
                bank=bank,
                obligation_type='loan',  # Example obligation type
                principal_amount=5000 * (i+1),
                interest_rate=5.0,  # Example interest rate
                payment_frequency='monthly',
                payment_amount=1000,  # Example payment amount
                total_payments=12,  # Example total payments
                start_date="2025-05-01",
                end_date="2026-05-01",
                created_by=self.user
            )

    def test_get_obligations(self):
        # Test retrieving bank obligations with authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.obligations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)  # Ensure count matches the number of items
        self.assertIsInstance(response.data['results'], list)  # Ensure 'results' is a list
        self.assertGreater(len(response.data['results']), 0)  # Ensure the list is not empty

# Create your tests here.
