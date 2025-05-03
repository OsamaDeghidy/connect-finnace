import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_system.settings')
django.setup()

# Import models after Django setup
from accounts.models import User
from accounts_receivable.models import Bank, Client, AccountReceivable, ReceivableTransaction
from accounts_payable.models import Supplier, AccountPayable, PayableTransaction, PaymentReminder
from bank_obligations.models import BankObligation, ObligationPayment
from cash_transactions.models import CashAccount, TransactionCategory, CashTransaction, CashAccountTransaction
from django.utils import timezone

# Get or create admin user
try:
    admin_user = User.objects.get(email='osama@example.com')
except User.DoesNotExist:
    print("Admin user not found. Please create one first.")
    exit(1)

print("Starting to add sample data...")

# Add Banks
banks_data = [
    {'name': 'البنك الأهلي السعودي', 'arabic_name': 'البنك الأهلي السعودي', 'branch': 'الرياض', 'swift_code': 'NCBKSAJE', 'contact_person': 'عبدالله محمد', 'phone': '+966501234567', 'email': 'contact@alahli.com', 'address': 'الرياض، طريق الملك فهد'},
    {'name': 'Riyad Bank', 'arabic_name': 'بنك الرياض', 'branch': 'جدة', 'swift_code': 'RIBLSARI', 'contact_person': 'سعد خالد', 'phone': '+966512345678', 'email': 'contact@riyadbank.com', 'address': 'جدة، شارع التحلية'},
    {'name': 'Al Rajhi Bank', 'arabic_name': 'مصرف الراجحي', 'branch': 'الدمام', 'swift_code': 'RJHISARI', 'contact_person': 'محمد علي', 'phone': '+966523456789', 'email': 'contact@alrajhibank.com', 'address': 'الدمام، شارع الملك خالد'},
]

banks = []
for bank_data in banks_data:
    bank, created = Bank.objects.get_or_create(
        name=bank_data['name'],
        defaults={
            'arabic_name': bank_data['arabic_name'],
            'branch': bank_data['branch'],
            'swift_code': bank_data['swift_code'],
            'contact_person': bank_data['contact_person'],
            'phone': bank_data['phone'],
            'email': bank_data['email'],
            'address': bank_data['address'],
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
    {'name': 'شركة الأفق للتجارة', 'arabic_name': 'شركة الأفق للتجارة', 'contact_person': 'أحمد محمد', 'email': 'ahmed@horizon.com', 'phone': '+966501234567', 'address': 'الرياض، حي العليا', 'tax_number': '300123456', 'credit_limit': 50000},
    {'name': 'Alnoor Contracting', 'arabic_name': 'مؤسسة النور للمقاولات', 'contact_person': 'خالد عبدالله', 'email': 'khalid@alnoor.com', 'phone': '+966512345678', 'address': 'جدة، حي الروضة', 'tax_number': '300234567', 'credit_limit': 75000},
    {'name': 'Creativity Tech', 'arabic_name': 'شركة الإبداع للتقنية', 'contact_person': 'سارة علي', 'email': 'sara@creativity.com', 'phone': '+966523456789', 'address': 'الدمام، حي الفيصلية', 'tax_number': '300345678', 'credit_limit': 100000},
]

clients = []
for client_data in clients_data:
    client, created = Client.objects.get_or_create(
        name=client_data['name'],
        defaults={
            'arabic_name': client_data['arabic_name'],
            'contact_person': client_data['contact_person'],
            'email': client_data['email'],
            'phone': client_data['phone'],
            'address': client_data['address'],
            'tax_number': client_data['tax_number'],
            'credit_limit': client_data['credit_limit'],
            'is_active': True,
            'notes': f'عميل تم إنشاؤه تلقائياً للاختبار',
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
    {'name': 'شركة التوريدات العامة', 'arabic_name': 'شركة التوريدات العامة', 'contact_person': 'محمد سعيد', 'email': 'mohammed@supplies.com', 'phone': '+966534567890', 'address': 'الرياض، حي الملز', 'tax_number': '310123456', 'payment_terms': 30},
    {'name': 'Supply Equipment Est.', 'arabic_name': 'مؤسسة الإمداد للتجهيزات', 'contact_person': 'فهد ناصر', 'email': 'fahad@supply.com', 'phone': '+966545678901', 'address': 'جدة، حي السلامة', 'tax_number': '310234567', 'payment_terms': 45},
    {'name': 'Future Equipment Co.', 'arabic_name': 'شركة المستقبل للمعدات', 'contact_person': 'نورة سعد', 'email': 'noura@future.com', 'phone': '+966556789012', 'address': 'الدمام، حي الشاطئ', 'tax_number': '310345678', 'payment_terms': 60},
]

suppliers = []
for supplier_data in suppliers_data:
    supplier, created = Supplier.objects.get_or_create(
        name=supplier_data['name'],
        defaults={
            'arabic_name': supplier_data['arabic_name'],
            'contact_person': supplier_data['contact_person'],
            'email': supplier_data['email'],
            'phone': supplier_data['phone'],
            'address': supplier_data['address'],
            'tax_number': supplier_data['tax_number'],
            'payment_terms': supplier_data['payment_terms'],
            'is_active': True,
            'notes': f'مورد تم إنشاؤه تلقائياً للاختبار',
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
    {'name': 'Main Cash', 'arabic_name': 'الصندوق الرئيسي', 'initial_balance': Decimal('50000.00'), 'description': 'الصندوق الرئيسي للشركة'},
    {'name': 'Petty Cash', 'arabic_name': 'حساب المصروفات اليومية', 'initial_balance': Decimal('5000.00'), 'description': 'حساب للمصروفات اليومية الصغيرة'},
    {'name': 'Emergency Fund', 'arabic_name': 'حساب الطوارئ', 'initial_balance': Decimal('20000.00'), 'description': 'حساب احتياطي للطوارئ'},
]

cash_accounts = []
for account_data in cash_accounts_data:
    account, created = CashAccount.objects.get_or_create(
        name=account_data['name'],
        defaults={
            'arabic_name': account_data['arabic_name'],
            'initial_balance': account_data['initial_balance'],
            'description': account_data['description'],
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
    {'name': 'Salaries', 'arabic_name': 'رواتب', 'category_type': 'expense', 'description': 'مدفوعات الرواتب للموظفين'},
    {'name': 'Rent', 'arabic_name': 'إيجارات', 'category_type': 'expense', 'description': 'إيجارات المكاتب والمستودعات'},
    {'name': 'Sales', 'arabic_name': 'مبيعات', 'category_type': 'income', 'description': 'إيرادات من المبيعات'},
    {'name': 'Consulting', 'arabic_name': 'استشارات', 'category_type': 'income', 'description': 'إيرادات من الخدمات الاستشارية'},
    {'name': 'Utilities', 'arabic_name': 'مرافق', 'category_type': 'expense', 'description': 'فواتير الكهرباء والماء والاتصالات'},
]

categories = []
for category_data in categories_data:
    category, created = TransactionCategory.objects.get_or_create(
        name=category_data['name'],
        defaults={
            'arabic_name': category_data['arabic_name'],
            'category_type': category_data['category_type'],
            'description': category_data['description'],
            'is_active': True
        }
    )
    categories.append(category)
    if created:
        print(f"Added transaction category: {category.name}")
    else:
        print(f"Transaction category already exists: {category.name}")

# Updated to check for existing data before creating new entries
# Add Account Receivables
for i in range(5):
    client = random.choice(clients)
    bank = random.choice(banks)
    transaction_date = timezone.now() - timedelta(days=random.randint(1, 30))
    due_date = transaction_date + timedelta(days=random.randint(15, 60))
    amount = Decimal(str(random.randint(5000, 50000)))
    check_number = f"CHK-{random.randint(1000, 9999)}"
    receipt_number = f"AR-{2025}-{i+1:05d}"
    
    receivable, created = AccountReceivable.objects.get_or_create(
        receipt_number=receipt_number,
        defaults={
            'client': client,
            'bank': bank,
            'amount': amount,
            'transaction_date': transaction_date,
            'due_date': due_date,
            'check_number': check_number,
            'status': random.choice(['active', 'completed', 'pending', 'overdue']),
            'notes': f"فاتورة مبيعات لـ {client.name}",
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"Added account receivable: {receivable.receipt_number}")
        
        # Add some transactions for this receivable
        if receivable.status in ['completed']:
            paid_amount = amount
            ReceivableTransaction.objects.create(
                receivable=receivable,
                transaction_type='full_payment',
                amount=paid_amount,
                transaction_date=transaction_date + timedelta(days=random.randint(1, 10)),
                reference=f"REF-{i+1:03d}",
                notes=f"دفعة كاملة من {client.name}",
                created_by=admin_user
            )
            print(f"Added receivable transaction for {receivable.receipt_number}")
        elif receivable.status == 'active':
            paid_amount = amount / 2
            ReceivableTransaction.objects.create(
                receivable=receivable,
                transaction_type='partial_payment',
                amount=paid_amount,
                transaction_date=transaction_date + timedelta(days=random.randint(1, 10)),
                reference=f"REF-{i+1:03d}",
                notes=f"دفعة جزئية من {client.name}",
                created_by=admin_user
            )
            print(f"Added receivable transaction for {receivable.receipt_number}")
    else:
        print(f"Account receivable already exists: {receivable.receipt_number}")

# Add Account Payables
for i in range(5):
    supplier = random.choice(suppliers)
    bank = random.choice(banks)
    transaction_date = timezone.now() - timedelta(days=random.randint(1, 30))
    due_date = transaction_date + timedelta(days=random.randint(15, 60))
    amount = Decimal(str(random.randint(3000, 30000)))
    check_number = f"CHK-{random.randint(1000, 9999)}"
    payment_number = f"AP-{2025}-{i+1:05d}"
    invoice_number = f"INV-S-{random.randint(1000, 9999)}"
    invoice_date = transaction_date - timedelta(days=random.randint(1, 5))
    
    payable, created = AccountPayable.objects.get_or_create(
        payment_number=payment_number,
        defaults={
            'supplier': supplier,
            'bank': bank,
            'amount': amount,
            'transaction_date': transaction_date,
            'due_date': due_date,
            'check_number': check_number,
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'description': f"فاتورة مشتريات من {supplier.name}",
            'status': random.choice(['scheduled', 'in_process', 'paid', 'delayed']),
            'notes': f"تم إنشاء هذا الحساب الدائن تلقائياً للاختبار",
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"Added account payable: {payable.payment_number}")
        
        # Add some transactions for this payable
        if payable.status in ['paid']:
            paid_amount = amount
            PayableTransaction.objects.create(
                payable=payable,
                transaction_type='full_payment',
                amount=paid_amount,
                transaction_date=transaction_date + timedelta(days=random.randint(1, 10)),
                reference=f"PAY-{i+1:03d}",
                notes=f"دفعة كاملة إلى {supplier.name}",
                created_by=admin_user
            )
            print(f"Added payable transaction for {payable.payment_number}")
        elif payable.status == 'in_process':
            paid_amount = amount / 2
            PayableTransaction.objects.create(
                payable=payable,
                transaction_type='partial_payment',
                amount=paid_amount,
                transaction_date=transaction_date + timedelta(days=random.randint(1, 10)),
                reference=f"PAY-{i+1:03d}",
                notes=f"دفعة جزئية إلى {supplier.name}",
                created_by=admin_user
            )
            print(f"Added payable transaction for {payable.payment_number}")
            
        # Add payment reminder for scheduled payables
        if payable.status == 'scheduled':
            for reminder_type in ['30_days', '15_days']:
                days_before = 30 if reminder_type == '30_days' else 15
                reminder_date = due_date - timedelta(days=days_before)
                PaymentReminder.objects.create(
                    payable=payable,
                    reminder_type=reminder_type,
                    reminder_date=reminder_date,
                    notes=f"تذكير بسداد فاتورة {supplier.name}",
                )
                print(f"Added payment reminder for {payable.payment_number}")
    else:
        print(f"Account payable already exists: {payment_number}")

# Add Bank Obligations
obligation_types = ['loan', 'credit_line', 'letter_of_credit']
payment_frequencies = ['monthly', 'quarterly', 'semi_annually', 'annually', 'lump_sum']
for i in range(3):
    bank = random.choice(banks)
    start_date = timezone.now() - timedelta(days=random.randint(30, 180))
    end_date = start_date + timedelta(days=random.randint(180, 365))
    principal_amount = Decimal(str(random.randint(100000, 500000)))
    obligation_type = obligation_types[i % len(obligation_types)]
    payment_frequency = random.choice(payment_frequencies)
    total_payments = 12 if payment_frequency == 'monthly' else 4 if payment_frequency == 'quarterly' else 2 if payment_frequency == 'semi_annually' else 1
    payment_amount = principal_amount / total_payments
    
    obligation, created = BankObligation.objects.get_or_create(
        obligation_number=f"BO-{2025}-{i+1:05d}",
        defaults={
            'obligation_type': obligation_type,
            'bank': bank,
            'branch': bank.branch,
            'account_number': f"ACC-{random.randint(10000, 99999)}",
            'principal_amount': principal_amount,
            'interest_rate': Decimal(str(random.uniform(3.0, 8.0))),
            'payment_frequency': payment_frequency,
            'payment_amount': payment_amount,
            'total_payments': total_payments,
            'start_date': start_date,
            'end_date': end_date,
            'purpose': f"تمويل مشروع {i+1}",
            'collateral': f"ضمانات للالتزام {i+1}",
            'notes': f"التزام مالي مع {bank.name} - تم إنشاؤه تلقائياً للاختبار"
        }
    )
    
    if created:
        print(f"Added bank obligation: {obligation.obligation_number}")
        
        # Add some payments for this obligation
        payment_count = min(random.randint(1, 3), total_payments)
        for j in range(payment_count):
            payment_date = start_date + timedelta(days=30 * (j + 1))
            payment_amount = principal_amount / Decimal(str(total_payments))
            interest_portion = payment_amount * (obligation.interest_rate / Decimal('100'))
            principal_portion = payment_amount - interest_portion
            
            ObligationPayment.objects.create(
                obligation=obligation,
                payment_date=payment_date,
                amount=payment_amount,
                principal_portion=principal_portion,
                interest_portion=interest_portion,
                reference_number=f"PAY-OB-{i+1:02d}-{j+1:02d}",
                notes=f"دفعة {j+1} للالتزام {obligation.obligation_number}"
            )
            print(f"Added obligation payment for {obligation.obligation_number}")
    else:
        print(f"Bank obligation already exists: {obligation.obligation_number}")

# Add Cash Transactions
for i in range(10):
    transaction_type = random.choice(['income', 'expense'])
    category = random.choice([c for c in categories if c.category_type == transaction_type])
    transaction_date = timezone.now() - timedelta(days=random.randint(1, 60))
    amount = Decimal(str(random.randint(500, 5000)))
    account = random.choice(cash_accounts)
    reference_number = f"CT-{2025}-{i+1:05d}"
    
    # Updated to use valid fields for CashTransaction
    transaction, created = CashTransaction.objects.get_or_create(
        reference_number=reference_number,
        defaults={
            'transaction_type': transaction_type,
            'category': category,
            'amount': amount,
            'transaction_date': transaction_date,
            'description': f"معاملة نقدية - {category.name}",
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"Added cash transaction: {transaction.reference_number}")
    else:
        print(f"Cash transaction already exists: {transaction.reference_number}")

print("Sample data added successfully!")

from django.core.management.base import BaseCommand
from accounts.models import User
from accounts_payable.models import AccountPayable
from accounts_receivable.models import AccountReceivable
from bank_obligations.models import BankObligation
from cash_transactions.models import CashTransaction

class Command(BaseCommand):
    help = 'Add sample data to the database'

    def handle(self, *args, **kwargs):
        # Add sample users
        user1 = User.objects.create_user(email='user1@example.com', password='password123')
        user2 = User.objects.create_user(email='user2@example.com', password='password123')

        # Add sample accounts payable
        AccountPayable.objects.create(name='Supplier A', amount=1000, due_date='2025-05-01', user=user1)
        AccountPayable.objects.create(name='Supplier B', amount=2000, due_date='2025-05-15', user=user2)

        # Add sample accounts receivable
        AccountReceivable.objects.create(name='Client A', amount=1500, due_date='2025-05-10', user=user1)
        AccountReceivable.objects.create(name='Client B', amount=2500, due_date='2025-05-20', user=user2)

        # Add sample bank obligations
        BankObligation.objects.create(name='Loan A', amount=5000, due_date='2025-06-01', user=user1)
        BankObligation.objects.create(name='Loan B', amount=7000, due_date='2025-06-15', user=user2)

        # Add sample cash transactions
        CashTransaction.objects.create(description='Office Supplies', amount=300, transaction_date='2025-04-28', user=user1)
        CashTransaction.objects.create(description='Travel Expenses', amount=500, transaction_date='2025-04-29', user=user2)

        self.stdout.write(self.style.SUCCESS('Sample data added successfully!'))
