from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import AccountPayable, Supplier
from accounts_receivable.models import Bank
import pytest

@pytest.fixture
def create_user(db):
    User = get_user_model()
    return User.objects.create_user(email="testuser@example.com", password="testpassword")

@pytest.fixture
def create_bank(db):
    return Bank.objects.create(
        name="Test Bank",
        branch="Main Branch",
        swift_code="TEST123",
        contact_person="John Doe",
        phone="+123456789",
        email="bank@example.com",
        address="123 Test Street"
    )

@pytest.fixture
def create_supplier(db):
    return Supplier.objects.create(
        name="Test Supplier",
        contact_person="Jane Doe",
        email="supplier@example.com",
        phone="+987654321",
        address="456 Supplier Lane",
        tax_number="TAX12345"
    )

@pytest.mark.django_db
def test_create_account_payable(create_user, create_bank, create_supplier):
    payable = AccountPayable.objects.create(
        supplier=create_supplier,
        bank=create_bank,
        amount=1000.00,
        due_date="2025-05-01",
        created_by=create_user
    )
    assert payable.supplier.name == "Test Supplier"
    assert payable.bank.name == "Test Bank"
    assert payable.amount == 1000.00
    assert str(payable.due_date) == "2025-05-01"

class AccountsPayableAPITestCase(APITestCase):
    def setUp(self):
        self.payables_url = '/api/v1/accounts-payable/payables/'
        self.login_url = '/api/v1/accounts/token/'
        self.user_data = {'email': 'testuser@example.com', 'password': 'testpassword'}

        # Create a test user and get JWT token
        User = get_user_model()
        self.user = User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.token = response.data['access']

        # Add sample data
        for i in range(5):
            supplier = Supplier.objects.create(
                name=f"Supplier {i+1}",
                contact_person=f"Contact {i+1}",
                email=f"supplier{i+1}@example.com",
                phone=f"+966500000{i+1}",
                address=f"Address {i+1}",
                tax_number=f"TAX{i+1}"
            )
            bank = Bank.objects.create(
                name=f"Bank {i+1}",
                branch=f"Branch {i+1}",
                swift_code=f"SWIFT{i+1}",
                contact_person=f"Contact {i+1}",
                phone=f"+966500000{i+1}",
                email=f"bank{i+1}@example.com",
                address=f"Address {i+1}"
            )
            AccountPayable.objects.create(
                supplier=supplier,
                bank=bank,  # Link the bank
                amount=1000 * (i+1),
                due_date="2025-05-01",
                created_by=self.user
            )

    def test_get_payables(self):
        # Test retrieving accounts payable with authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.payables_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)  # Ensure count matches the number of items
        self.assertIsInstance(response.data['results'], list)  # Ensure 'results' is a list
        self.assertGreater(len(response.data['results']), 0)  # Ensure the list is not empty

# Create your tests here.
