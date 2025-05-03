import os
import django
import random
from decimal import Decimal
from datetime import timedelta, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_system.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts_receivable.models import Bank, Client, AccountReceivable, ReceivableTransaction
from accounts_payable.models import Supplier, AccountPayable, PayableTransaction, PaymentReminder
from cash_transactions.models import CashAccount, TransactionCategory, CashTransaction, CashAccountTransaction

User = get_user_model()

print("Starting to add sample data...")

# Get or create admin user
admin_user, created = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("Created admin user")
else:
    print("Admin user already exists")

# Add Banks
banks_data = [
    {'name': 'Saudi National Bank', 'arabic_name': 'البنك الأهلي السعودي', 'branch': 'Riyadh Main Branch'},
    {'name': 'Riyad Bank', 'arabic_name': 'بنك الرياض', 'branch': 'Jeddah Branch'},
    {'name': 'Al Rajhi Bank', 'arabic_name': 'مصرف الراجحي', 'branch': 'Dammam Branch'},
]

banks = []
for bank_data in banks_data:
    bank, created = Bank.objects.get_or_create(
        name=bank_data['name'],
        defaults={
            'arabic_name': bank_data['arabic_name'],
            'branch': bank_data['branch'],
            'is_active': True
        }
    )
    banks.append(bank)
    if created:
        print(f"Added bank: {bank.name}")
    else:
        print(f"Bank already exists: {bank.name}")

# Add Clients
clients_data = [
    {'name': 'Horizon Trading Co.', 'arabic_name': 'شركة الأفق للتجارة', 'credit_limit': Decimal('100000.00')},
    {'name': 'Alnoor Contracting', 'arabic_name': 'شركة النور للمقاولات', 'credit_limit': Decimal('150000.00')},
    {'name': 'Creativity Tech', 'arabic_name': 'شركة الإبداع للتقنية', 'credit_limit': Decimal('80000.00')},
]

clients = []
for client_data in clients_data:
    client, created = Client.objects.get_or_create(
        name=client_data['name'],
        defaults={
            'arabic_name': client_data['arabic_name'],
            'credit_limit': client_data['credit_limit'],
            'is_active': True,
            'created_by': admin_user
        }
    )
    clients.append(client)
    if created:
        print(f"Added client: {client.name}")
    else:
        print(f"Client already exists: {client.name}")

# Add Suppliers
suppliers_data = [
    {'name': 'General Supplies Co.', 'arabic_name': 'شركة التوريدات العامة', 'payment_terms': 30},
    {'name': 'Supply Equipment Est.', 'arabic_name': 'مؤسسة توريد المعدات', 'payment_terms': 45},
    {'name': 'Future Equipment Co.', 'arabic_name': 'شركة معدات المستقبل', 'payment_terms': 60},
]

suppliers = []
for supplier_data in suppliers_data:
    supplier, created = Supplier.objects.get_or_create(
        name=supplier_data['name'],
        defaults={
            'arabic_name': supplier_data['arabic_name'],
            'payment_terms': supplier_data['payment_terms'],
            'is_active': True,
            'created_by': admin_user
        }
    )
    suppliers.append(supplier)
    if created:
        print(f"Added supplier: {supplier.name}")
    else:
        print(f"Supplier already exists: {supplier.name}")

# Add Cash Accounts
cash_accounts_data = [
    {'name': 'Main Cash', 'arabic_name': 'الصندوق الرئيسي', 'initial_balance': Decimal('50000.00')},
    {'name': 'Petty Cash', 'arabic_name': 'حساب المصروفات اليومية', 'initial_balance': Decimal('5000.00')},
]

cash_accounts = []
for account_data in cash_accounts_data:
    account, created = CashAccount.objects.get_or_create(
        name=account_data['name'],
        defaults={
            'arabic_name': account_data['arabic_name'],
            'initial_balance': account_data['initial_balance'],
            'is_active': True
        }
    )
    cash_accounts.append(account)
    if created:
        print(f"Added cash account: {account.name}")
    else:
        print(f"Cash account already exists: {account.name}")

# Add Transaction Categories
categories_data = [
    {'name': 'Salaries', 'arabic_name': 'رواتب', 'category_type': 'expense'},
    {'name': 'Sales', 'arabic_name': 'مبيعات', 'category_type': 'income'},
]

categories = []
for category_data in categories_data:
    category, created = TransactionCategory.objects.get_or_create(
        name=category_data['name'],
        defaults={
            'arabic_name': category_data['arabic_name'],
            'category_type': category_data['category_type'],
            'is_active': True
        }
    )
    categories.append(category)
    if created:
        print(f"Added transaction category: {category.name}")
    else:
        print(f"Transaction category already exists: {category.name}")

# Add Account Receivables
for i in range(2):
    client = random.choice(clients)
    bank = random.choice(banks)
    transaction_date = date.today() - timedelta(days=random.randint(1, 30))
    due_date = transaction_date + timedelta(days=random.randint(15, 60))
    amount = Decimal(str(random.randint(5000, 50000)))
    check_number = f"CHK-{random.randint(1000, 9999)}"
    
    try:
        receivable = AccountReceivable.objects.create(
            client=client,
            bank=bank,
            amount=amount,
            transaction_date=transaction_date,
            due_date=due_date,
            check_number=check_number,
            status='active',
            notes=f"فاتورة مبيعات لـ {client.name}",
            created_by=admin_user
        )
        print(f"Added account receivable: {receivable.receipt_number}")
    except Exception as e:
        print(f"Error adding receivable: {str(e)}")

# Add Account Payables
for i in range(2):
    supplier = random.choice(suppliers)
    bank = random.choice(banks)
    transaction_date = date.today() - timedelta(days=random.randint(1, 30))
    due_date = transaction_date + timedelta(days=random.randint(15, 60))
    amount = Decimal(str(random.randint(3000, 30000)))
    check_number = f"CHK-{random.randint(1000, 9999)}"
    invoice_number = f"INV-S-{random.randint(1000, 9999)}"
    invoice_date = transaction_date - timedelta(days=random.randint(1, 5))
    
    try:
        payable = AccountPayable.objects.create(
            supplier=supplier,
            bank=bank,
            amount=amount,
            transaction_date=transaction_date,
            due_date=due_date,
            check_number=check_number,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            status='scheduled',
            notes=f"فاتورة مشتريات من {supplier.name}",
            created_by=admin_user
        )
        print(f"Added account payable: {payable.payment_number}")
    except Exception as e:
        print(f"Error adding payable: {str(e)}")

# Add Cash Transactions
for i in range(4):
    transaction_type = random.choice(['income', 'expense'])
    category = random.choice([c for c in categories if c.category_type == transaction_type])
    transaction_date = date.today() - timedelta(days=random.randint(1, 60))
    amount = Decimal(str(random.randint(500, 5000)))
    account = random.choice(cash_accounts)
    
    try:
        # Create the transaction
        transaction = CashTransaction.objects.create(
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            transaction_date=transaction_date,
            description=f"معاملة نقدية - {category.name}",
            created_by=admin_user
        )
        
        # Link transaction to cash account
        CashAccountTransaction.objects.create(
            account=account,
            transaction=transaction,
            amount=amount,
            notes=f"تم إنشاء هذه المعاملة تلقائياً للاختبار"
        )
        
        print(f"Added cash transaction: {transaction.reference_number}")
    except Exception as e:
        print(f"Error adding cash transaction: {str(e)}")

print("Sample data added successfully!")
