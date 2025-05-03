from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import AccountReceivable, Client, Bank

class AccountsReceivableAPITestCase(APITestCase):
    def setUp(self):
        self.receivables_url = '/api/v1/accounts-receivable/receivables/'
        self.login_url = '/api/v1/accounts/token/'
        self.user_data = {'email': 'testuser@example.com', 'password': 'testpassword'}

        # Create a test user and get JWT token
        User = get_user_model()
        self.user = User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.token = response.data['access']

        # Add sample data
        for i in range(5):
            client = Client.objects.create(
                name=f"Client {i+1}",
                contact_person=f"Contact {i+1}",
                email=f"client{i+1}@example.com",
                phone=f"+966500000{i+1}",
                address=f"Address {i+1}",
                tax_number=f"TAX{i+1}"
            )
            bank = Bank.objects.create(
                name=f"Bank {i+1}",
                branch=f"Branch {i+1}",
                swift_code=f"SWIFT{i+1}",
                contact_person=f"Contact {i+1}",
                phone=f"+966500000{i+1}"
            )
            AccountReceivable.objects.create(
                client=client,
                bank=bank,  # Link the bank
                amount=1500 * (i+1),
                due_date="2025-05-10",
                created_by=self.user
            )

    def test_get_receivables(self):
        # Test retrieving accounts receivable with authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.receivables_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)  # Ensure count matches the number of items
        self.assertIsInstance(response.data['results'], list)  # Ensure 'results' is a list
        self.assertGreater(len(response.data['results']), 0)  # Ensure the list is not empty

# Create your tests here.
