# Electronic Health Software (EHS) Backend

A comprehensive healthcare management system backend built with Django REST Framework, focusing on Indian healthcare requirements and international compliance standards.

## 🚀 Features

### 1. Authentication & User Management
- **Multi-role Support**: Doctors, Administrators, Patients, Staff
- **Secure Authentication**: JWT-based with refresh tokens
- **Multi-Factor Authentication (MFA)**
- **Audit Logging**: HIPAA-compliant action tracking

#### APIs
```http
POST /api/users/register/
POST /api/users/login/
POST /api/users/refresh-token/
POST /api/users/mfa/enable/
POST /api/users/mfa/verify/
GET /api/users/audit-logs/
```

### 2. Patient Management
- **Complete Patient Profiles**
- **Medical History Tracking**
- **Document Management**
- **FHIR/HL7 Integration**

#### APIs
```http
GET /api/patients/
POST /api/patients/
GET /api/patients/{id}/
PUT /api/patients/{id}/
GET /api/patients/{id}/medical-history/
POST /api/patients/{id}/documents/
GET /api/patients/{id}/fhir/
POST /api/patients/hl7/import/
```

### 3. Appointment Management
- **Calendar-based Scheduling**
- **Conflict Detection**
- **Status Tracking**

#### APIs
```http
GET /api/appointments/
POST /api/appointments/
GET /api/appointments/{id}/
PUT /api/appointments/{id}/status/
GET /api/appointments/doctor/{doctor_id}/schedule/
```

### 4. Billing & Payments
- **Invoice Generation**
- **Payment Processing**
- **Financial Records**

#### APIs
```http
POST /api/billing/invoices/
GET /api/billing/invoices/{id}/
POST /api/billing/payments/
GET /api/billing/invoices/{id}/payments/
```

### 5. Analytics & Reporting
- **Patient Demographics**
- **Financial Analytics**
- **Appointment Statistics**

#### APIs
```http
GET /api/analytics/patients/demographics/
GET /api/analytics/financial/summary/
GET /api/analytics/appointments/statistics/
```

## 🔒 Security Features

- End-to-end encryption
- Role-based access control (RBAC)
- HIPAA compliance measures
- Audit logging
- Data encryption at rest
- Secure file storage

## 🧪 Test Coverage

### 1. User Management Tests
```python
class UserModelTests(TestCase):
    - test_user_creation()
    - test_user_permissions()

class AuditLogTests(TestCase):
    - test_audit_log_creation()
```

### 2. Patient Management Tests
```python
class PatientModelTests(TestCase):
    - test_patient_creation()
    - test_fhir_conversion()

class DocumentTests(TestCase):
    - test_document_creation()

class TestHL7Integration:
    - test_hl7_message_parsing()
```

### 3. Appointment Tests
```python
class AppointmentTests(TestCase):
    - test_appointment_creation()
    - test_appointment_slot_conflict()
```

### 4. Billing Tests
```python
class BillingTests(TestCase):
    - test_invoice_creation()
    - test_payment_processing()
```

## 🛠 Technical Stack

- **Framework**: Django 5.0.1
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL
- **Cache & Queue**: Redis, Celery
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Storage**: Django Storages (AWS S3 compatible)
- **Monitoring**: Sentry
- **Healthcare Standards**: FHIR, HL7
- **Testing**: pytest, Django Test Framework

## 🚀 Getting Started

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start development server:
   ```bash
   python manage.py runserver
   ```

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

## 🧪 Running Tests

```bash
# Run all tests with coverage
pytest --cov

# Run specific test module
pytest tests/test_users.py
```

## 📝 API Documentation

API documentation is available at `/api/docs/` when running the server.

## 🔐 Compliance

- HIPAA (Health Insurance Portability and Accountability Act)
- GDPR (General Data Protection Regulation)
- India DPDP (Digital Personal Data Protection)

## 📊 Monitoring

- Application monitoring via Sentry
- Comprehensive audit logging
- Performance metrics tracking

## 🔄 Data Integration

- FHIR (Fast Healthcare Interoperability Resources) support
- HL7 (Health Level 7) message processing
- Support for standard medical imaging formats (DICOM)