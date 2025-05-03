from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import CashTransaction, TransactionCategory

class CashTransactionsAPITestCase(APITestCase):
    def setUp(self):
        self.transactions_url = '/api/v1/cash-transactions/transactions/'
        self.login_url = '/api/v1/accounts/token/'
        self.user_data = {'email': 'testuser@example.com', 'password': 'testpassword'}

        # Create a test user and get JWT token
        User = get_user_model()
        self.user = User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.token = response.data['access']

        # Add sample data
        category = TransactionCategory.objects.create(
            name="Test Category",
            category_type="income",
            description="Test Description"
        )
        for i in range(10):
            CashTransaction.objects.create(
                category=category,
                description=f"Transaction {i+1}",
                amount=300 * (i+1),
                transaction_date="2025-04-28",
                transaction_type="income",  # Ensure it matches the category type
                created_by=self.user
            )

    def test_get_transactions(self):
        # Test retrieving cash transactions with authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)  # Ensure count matches the number of items
        self.assertIsInstance(response.data['results'], list)  # Ensure 'results' is a list
        self.assertGreater(len(response.data['results']), 0)  # Ensure the list is not empty
