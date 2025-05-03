# Backend Documentation - Financial Management System

## Overview

The backend of the **Financial Management System** is built using **Django** and provides a RESTful API for managing financial operations. It includes modules for accounts receivable, accounts payable, bank obligations, cash transactions, and more. The backend is optimized for Arabic-speaking businesses and supports features like authentication, authorization, and reporting.

---

## Project Structure

```
server/
├── accounts/               # User management and authentication
├── accounts_payable/       # Accounts payable management
├── accounts_receivable/    # Accounts receivable management
├── bank_obligations/       # Bank obligations management
├── cash_transactions/      # Cash transactions management
├── finance_calendar/       # Calendar events for financial tracking
├── finance_system/         # Core Django project settings
├── templates/              # HTML templates for admin and other views
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
```

---

## Modules and APIs

### 1. **Accounts**
- **Purpose**: Manages user authentication, roles, and login history.
- **Key Features**:
  - Custom user model with email-based authentication.
  - Two-factor authentication (2FA) support.
  - Login history tracking.
- **APIs**:
  - **`POST /accounts/token/`**: Obtain JWT token.
    - **Inputs**:
      - `email` (string): User's email.
      - `password` (string): User's password.
    - **Outputs**:
      - `access` (string): JWT access token.
      - `refresh` (string): JWT refresh token.
  - **`GET /accounts/users/`**: Retrieve a list of users.
    - **Outputs**:
      - List of user objects with fields: `id`, `email`, `is_active`, etc.
  - **`POST /accounts/password/change/`**: Change password.
    - **Inputs**:
      - `old_password` (string): Current password.
      - `new_password` (string): New password.
    - **Outputs**:
      - Success message.
  - **`POST /accounts/password/reset/`**: Request password reset.
    - **Inputs**:
      - `email` (string): User's email.
    - **Outputs**:
      - Success message.

### 2. **Accounts Payable**
- **Purpose**: Tracks payments owed to suppliers.
- **Key Features**:
  - Supplier management.
  - Payment reminders.
  - Payable transactions.
- **APIs**:
  - **`GET /payables/`**: Retrieve a list of accounts payable.
    - **Outputs**:
      - List of payable objects with fields: `id`, `supplier`, `amount`, `due_date`, etc.
  - **`POST /payables/`**: Create a new payable.
    - **Inputs**:
      - `supplier` (integer): Supplier ID.
      - `amount` (decimal): Amount owed.
      - `due_date` (date): Due date for payment.
    - **Outputs**:
      - Created payable object.
  - **`GET /payables/transactions/`**: Retrieve payable transactions.
    - **Outputs**:
      - List of transaction objects with fields: `id`, `payable`, `amount`, `transaction_date`, etc.
  - **`POST /reminders/`**: Create a payment reminder.
    - **Inputs**:
      - `payable` (integer): Payable ID.
      - `reminder_date` (date): Date for the reminder.
    - **Outputs**:
      - Created reminder object.

### 3. **Accounts Receivable**
- **Purpose**: Tracks payments owed by clients.
- **Key Features**:
  - Client management.
  - Receivable transactions.
  - Dashboard summary and reporting.
- **APIs**:
  - **`GET /receivables/`**: Retrieve a list of accounts receivable.
    - **Outputs**:
      - List of receivable objects with fields: `id`, `client`, `amount`, `due_date`, etc.
  - **`POST /receivables/`**: Create a new receivable.
    - **Inputs**:
      - `client` (integer): Client ID.
      - `amount` (decimal): Amount owed.
      - `due_date` (date): Due date for payment.
    - **Outputs**:
      - Created receivable object.
  - **`GET /dashboard/summary/`**: Retrieve dashboard summary.
    - **Outputs**:
      - Summary data including total receivables, overdue amounts, etc.
  - **`GET /reports/receivables/`**: Generate receivables report.
    - **Outputs**:
      - PDF or CSV report file.

### 4. **Bank Obligations**
- **Purpose**: Manages loans, credit lines, and other bank obligations.
- **Key Features**:
  - Obligation tracking.
  - Payment schedules.
  - Reporting.
- **APIs**:
  - **`GET /obligations/`**: Retrieve a list of bank obligations.
    - **Outputs**:
      - List of obligation objects with fields: `id`, `bank`, `amount`, `due_date`, etc.
  - **`POST /obligations/`**: Create a new obligation.
    - **Inputs**:
      - `bank` (integer): Bank ID.
      - `amount` (decimal): Obligation amount.
      - `due_date` (date): Due date for the obligation.
    - **Outputs**:
      - Created obligation object.
  - **`GET /obligations/payments/`**: Retrieve obligation payments.
    - **Outputs**:
      - List of payment objects with fields: `id`, `obligation`, `amount`, `payment_date`, etc.
  - **`GET /reports/obligations/`**: Generate obligation report.
    - **Outputs**:
      - PDF or CSV report file.

### 5. **Cash Transactions**
- **Purpose**: Tracks cash inflows and outflows.
- **Key Features**:
  - Transaction categories.
  - Cash account management.
  - Reporting and cash flow analysis.
- **APIs**:
  - **`GET /transactions/`**: Retrieve a list of cash transactions.
    - **Outputs**:
      - List of transaction objects with fields: `id`, `category`, `amount`, `transaction_date`, etc.
  - **`POST /transactions/`**: Create a new cash transaction.
    - **Inputs**:
      - `category` (string): Transaction category.
      - `amount` (decimal): Transaction amount.
      - `transaction_date` (date): Date of the transaction.
    - **Outputs**:
      - Created transaction object.
  - **`GET /reports/cash-flow/`**: Generate cash flow report.
    - **Outputs**:
      - PDF or CSV report file.

### 6. **Finance Calendar**
- **Purpose**: Tracks financial events and deadlines.
- **Key Features**:
  - Calendar event management.
- **APIs**:
  - Not explicitly defined in the current implementation.

---

## Completed Features

1. **Authentication**:
   - JWT-based authentication with 2FA support.
   - Password reset and change functionality.

2. **Core Modules**:
   - Accounts receivable and payable management.
   - Bank obligations tracking.
   - Cash transactions and reporting.

3. **Admin Panel**:
   - Custom admin views for all modules.
   - Inline editing for related models.

4. **Reporting**:
   - Dashboard summaries for receivables and payables.
   - Detailed reports for transactions and obligations.

---

## Issues and Improvements

### **Issues**
1. **Security**:
   - The `SECRET_KEY` is hardcoded in `.env` and should be replaced in production.
   - CSRF and session cookies are not fully secured in development mode.

2. **Testing**:
   - Minimal test coverage (`tests.py` files are mostly empty).

3. **Error Handling**:
   - Limited error handling in API views.

4. **Documentation**:
   - Lack of API documentation for endpoints.

---

### **Improvements**
1. **Security**:
   - Enforce HTTPS in production.
   - Use environment variables for sensitive data.
   - Implement stricter password policies.

2. **Testing**:
   - Add unit and integration tests for all modules.
   - Use tools like `pytest` for better test management.

3. **Performance**:
   - Optimize database queries in reporting endpoints.
   - Implement caching for frequently accessed data.

4. **Documentation**:
   - Use tools like Swagger or DRF-YASG to auto-generate API documentation.

---

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
   ```bash
   cd server
   python -m venv venv
    venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

---

## Technical Requirements

- **Database**: PostgreSQL (currently SQLite in development).
- **Authentication**: JWT with 2FA.
- **Performance**:
  - Page load: <3 seconds.
  - Real-time updates: <1 second delay.
  - Search results: <500ms response.

---

## Contributors

- **Osama** - Lead Developer
- **Team Members** - Backend and Frontend Developers

---

## License

This project is licensed under the MIT License.





echo "# connect-finnace" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/OsamaDeghidy/connect-finnace.git
git push -u origin main
…or push an existing repository from the command line
git remote add origin https://github.com/OsamaDeghidy/connect-finnace.git
git branch -M main
git push -u origin main