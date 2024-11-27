# Electronic Health Software (EHS) Backend

A comprehensive healthcare management system built with Django, designed for hospitals in India.

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client Apps   │────▶│   API Gateway   │────▶│ Django Backend  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ElastiCache    │◀───▶│    Celery      │◀───▶│      RDS        │
│    (Redis)      │     │   Workers       │     │  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                        ▲
         │                      │                        │
         ▼                      ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      SQS        │     │      S3         │     │    Sentry       │
│  Message Queue  │     │  File Storage   │     │   Monitoring    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Component Details

1. **Django Backend**
   - Core application logic
   - REST API endpoints
   - Authentication & Authorization
   - Data validation & processing

2. **Redis (ElastiCache)**
   - Session management
   - Cache layer
   - Rate limiting
   - Real-time notifications

3. **Celery Workers**
   - Asynchronous task processing
   - Document processing
   - Email notifications
   - Report generation

4. **PostgreSQL (RDS)**
   - Primary database
   - Patient records
   - Medical history
   - Appointment data

5. **AWS Services Integration**
   - S3: Document storage
   - SQS: Message queuing
   - CloudWatch: Monitoring
   - IAM: Access management

## 🔐 Authentication & Security

### JWT Authentication Flow

1. **Login Request**
```http
POST /api/users/login/
Content-Type: application/json

{
    "username": "doctor@example.com",
    "password": "secure_password"
}
```

2. **Response with Tokens**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

3. **Using Access Token**
```javascript
// Frontend API call example
const response = await fetch('/api/patients/', {
    headers: {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json'
    }
});
```

4. **Refresh Token Usage**
```http
POST /api/users/refresh-token/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Security Features
- JWT with short-lived access tokens (1 hour)
- Refresh tokens for extended sessions (1 day)
- Role-based access control (RBAC)
- Multi-Factor Authentication (MFA)
- HIPAA-compliant audit logging
- Rate limiting
- SSL/TLS encryption

## 🚀 AWS Deployment Guide

### Prerequisites
1. AWS Account with required permissions
2. AWS CLI configured
3. Docker installed
4. kubectl configured

### Infrastructure Setup

1. **VPC Configuration**
```bash
# Create VPC with public and private subnets
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.2.0/24
```

2. **RDS Setup**
```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier ehs-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password <password> \
    --allocated-storage 20
```

3. **ElastiCache Setup**
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id ehs-redis \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1
```

4. **S3 Bucket**
```bash
# Create bucket
aws s3 mb s3://ehs-documents

# Configure CORS
aws s3api put-bucket-cors --bucket ehs-documents \
    --cors-configuration file://cors.json
```

5. **SQS Queue**
```bash
# Create queue
aws sqs create-queue --queue-name ehs-tasks
```

### Application Deployment

1. **Build Docker Image**
```bash
docker build -t ehs-backend .
docker tag ehs-backend:latest <aws-account-id>.dkr.ecr.region.amazonaws.com/ehs-backend
```

2. **Push to ECR**
```bash
aws ecr get-login-password --region region | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.region.amazonaws.com
docker push <aws-account-id>.dkr.ecr.region.amazonaws.com/ehs-backend
```

3. **Deploy to ECS**
```bash
aws ecs create-service \
    --cluster ehs-cluster \
    --service-name ehs-service \
    --task-definition ehs-task \
    --desired-count 2
```

## 📡 API Documentation

### Authentication APIs
```http
POST   /api/users/register/        # New user registration
POST   /api/users/login/           # User login
POST   /api/users/refresh-token/   # Refresh JWT token
POST   /api/users/mfa/enable/      # Enable MFA
POST   /api/users/mfa/verify/      # Verify MFA token
```

### Patient Management APIs
```http
GET    /api/patients/              # List patients
POST   /api/patients/              # Create patient
GET    /api/patients/{id}/         # Get patient details
PUT    /api/patients/{id}/         # Update patient
GET    /api/patients/{id}/medical-history/  # Get medical history
POST   /api/patients/{id}/documents/        # Upload document
GET    /api/patients/{id}/fhir/    # Get FHIR data
POST   /api/patients/hl7/import/   # Import HL7 message
```

### Appointment APIs
```http
GET    /api/appointments/          # List appointments
POST   /api/appointments/          # Create appointment
PUT    /api/appointments/{id}/     # Update appointment
GET    /api/appointments/doctor/{id}/schedule/  # Get doctor schedule
```

### Billing APIs
```http
GET    /api/billing/invoices/      # List invoices
POST   /api/billing/invoices/      # Create invoice
GET    /api/billing/invoices/{id}/payments/  # Get invoice payments
POST   /api/billing/payments/      # Process payment
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_patients.py
```

### Test Categories

1. **Unit Tests**
   - Models
   - Services
   - Utilities
   - Serializers

2. **Integration Tests**
   - API endpoints
   - Database operations
   - File operations
   - External service integrations

3. **Authentication Tests**
   - Login/Logout
   - Token management
   - Permission checks
   - MFA verification

4. **Patient Management Tests**
   - CRUD operations
   - Document handling
   - Medical history
   - FHIR/HL7 integration

5. **Appointment Tests**
   - Scheduling
   - Conflict detection
   - Status updates
   - Calendar operations

6. **Billing Tests**
   - Invoice generation
   - Payment processing
   - Tax calculations
   - Report generation

### Test Results Example
```
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.0
plugins: cov-4.1.0, django-4.7.0
collected 89 items

tests/test_analytics_api.py ........                                   [  8%]
tests/test_appointments_api.py ..........                             [ 20%]
tests/test_billing_api.py .........                                   [ 30%]
tests/test_patients_api.py ...................                        [ 51%]
tests/test_patients.py ....................                           [ 73%]
tests/test_users.py .................                                 [ 92%]
tests/test_appointments.py ........                                   [100%]

----------- coverage: platform linux, python 3.11.0-final-0 -----------
Name                            Stmts   Miss  Cover
---------------------------------------------------
patients/models.py                125      4    97%
patients/services.py              89       6    93%
patients/views.py                 178     12    93%
appointments/models.py            45       2    96%
billing/models.py                 67       4    94%
users/models.py                   89       5    94%
---------------------------------------------------
TOTAL                            593     33    94%
```

## 📚 Additional Resources

- [API Documentation](https://api-docs.ehs-system.com)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)
- [Security Guidelines](https://www.hipaa.com/)