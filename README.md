# Menstrual Cycle Tracking App - Microservices Architecture

A research prototype demonstrating microservices architecture patterns for a Master's thesis comparing Modular Monolith vs Microservices architectures.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Microservices Patterns Demonstrated](#microservices-patterns-demonstrated)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [Testing the System](#testing-the-system)
- [Microservices Analysis](#microservices-analysis)

---

## Architecture Overview

This application implements a **microservices architecture** with 4 independent services communicating through REST APIs and asynchronous messaging.

### System Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Client/User   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  nginx Gateway  │
                                    │   (Port 80)     │
                                    └────────┬────────┘
                                             │
                ┌────────────────────────────┼────────────────────────────┐
                │                            │                            │
        ┌───────▼────────┐         ┌────────▼────────┐         ┌────────▼────────┐
        │  User Service  │         │ Cycle Tracking  │         │   Analytics     │
        │   (Port 5001)  │         │   (Port 5002)   │         │  (Port 5003)    │
        └───────┬────────┘         └────────┬────────┘         └────────┬────────┘
                │                           │                            │
                │                           │ Publishes                  │ Publishes
                │                           │ Cycle Events               │ Predictions
                │                           │                            │
                │                  ┌────────▼────────┐          ┌────────▼────────┐
                │                  │    RabbitMQ     │◄─────────┤  Notification   │
                │                  │  Message Queue  │          │   (Port 5004)   │
                │                  └─────────────────┘          └─────────────────┘
                │                           │                            │
        ┌───────▼────────┐         ┌───────▼────────┐         ┌────────▼────────┐
        │  PostgreSQL    │         │  PostgreSQL    │         │   PostgreSQL    │
        │   (User DB)    │         │  (Cycle DB)    │         │ (Analytics DB)  │
        └────────────────┘         └────────────────┘         └─────────────────┘
                                                                        │
                                                               ┌────────▼────────┐
                                                               │   PostgreSQL    │
                                                               │(Notification DB)│
                                                               └─────────────────┘
```

### Service Responsibilities

| Service | Port | Purpose | Database | Message Queue Role |
|---------|------|---------|----------|-------------------|
| **User Service** | 5001 | Authentication, user management | user-db | None |
| **Cycle Tracking Service** | 5002 | Period logging, symptoms tracking | cycle-db | **Publisher** (cycle events) |
| **Analytics Service** | 5003 | Predictions, insights, pattern analysis | analytics-db | **Consumer** (cycle events) + **Publisher** (predictions) |
| **Notification Service** | 5004 | Period reminders, notification management | notification-db | **Consumer** (prediction events) |

---

## Microservices Patterns Demonstrated

This implementation showcases the following microservices patterns:

### 1. **Database-per-Service Pattern**
- ✅ Each service has its **own PostgreSQL database**
- ✅ **Data isolation**: Services don't share databases
- ✅ **Independent scaling**: Each database can be scaled independently
- ✅ **Technology diversity**: Each service could use different database types

**Implementation:**
- `user-db` → User Service
- `cycle-db` → Cycle Tracking Service
- `analytics-db` → Analytics Service
- `notification-db` → Notification Service

### 2. **API Gateway Pattern**
- ✅ **Single entry point** for all client requests
- ✅ **Request routing** to appropriate services
- ✅ **Load balancing** capabilities
- ✅ **Centralized SSL termination** (production-ready)

**Implementation:** nginx reverse proxy on port 80

### 3. **Event-Driven Architecture**
- ✅ **Asynchronous communication** via RabbitMQ
- ✅ **Loose coupling** between services
- ✅ **Event publishing and consumption**
- ✅ **Message persistence** for reliability

**Event Flow:**
1. Cycle Tracking Service → **publishes** `cycle.new` events
2. Analytics Service → **consumes** cycle events, generates predictions
3. Analytics Service → **publishes** `prediction.new` events
4. Notification Service → **consumes** prediction events, creates reminders

### 4. **Service Independence**
- ✅ Each service can be **deployed independently**
- ✅ Services run in **separate containers**
- ✅ **Independent scaling** per service
- ✅ **Technology flexibility**: Different Python versions, frameworks possible

### 5. **Distributed Authentication**
- ✅ **JWT-based authentication** with shared secret
- ✅ **Stateless authentication**: No session storage needed
- ✅ Each service validates tokens **independently**
- ✅ **Horizontal scalability**: No session affinity required

### 6. **Health Check Pattern**
- ✅ Each service exposes `/health` endpoint
- ✅ Container orchestration uses health checks
- ✅ Automatic **service recovery** on failure
- ✅ **Monitoring and alerting** capabilities

### 7. **Service Discovery**
- ✅ Services communicate via **Docker network**
- ✅ **DNS-based discovery**: Services referenced by name
- ✅ No hardcoded IPs required

---

## Technology Stack

### Backend Services
- **Python 3.11+**
- **Flask** - Lightweight web framework
- **Flask-RESTful** - REST API development
- **SQLAlchemy** - ORM for database operations
- **PyJWT** - JWT token generation and validation
- **Pika** - RabbitMQ client library

### Infrastructure
- **PostgreSQL 15** - Relational database (4 instances)
- **RabbitMQ 3** - Message broker with management UI
- **nginx** - API Gateway and reverse proxy
- **Docker & Docker Compose** - Containerization and orchestration

---

## Project Structure

```
menstrual-cycle-tracker/
├── services/
│   ├── user-service/
│   │   ├── app.py                  # Flask application
│   │   ├── models.py               # Database models
│   │   ├── routes.py               # API endpoints
│   │   ├── auth.py                 # JWT authentication
│   │   ├── config.py               # Configuration
│   │   ├── requirements.txt        # Python dependencies
│   │   └── Dockerfile              # Container definition
│   │
│   ├── cycle-tracking-service/
│   │   ├── app.py
│   │   ├── models.py               # Cycle and Symptom models
│   │   ├── routes.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── message_queue.py        # RabbitMQ publisher
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── analytics-service/
│   │   ├── app.py
│   │   ├── models.py               # Analytics and Prediction models
│   │   ├── routes.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── prediction_engine.py    # Prediction algorithms
│   │   ├── message_queue.py        # RabbitMQ consumer + publisher
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── notification-service/
│       ├── app.py
│       ├── models.py               # Notification and Preference models
│       ├── routes.py
│       ├── auth.py
│       ├── config.py
│       ├── notification_manager.py # Notification logic
│       ├── message_queue.py        # RabbitMQ consumer
│       ├── requirements.txt
│       └── Dockerfile
│
├── gateway/
│   └── nginx/
│       └── nginx.conf              # API Gateway configuration
│
├── docker-compose.yml              # Service orchestration
├── .env.example                    # Environment variables template
├── .gitignore
└── README.md
```

---

## Setup Instructions

### Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git**

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd menstrual-cycle-tracker
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set JWT_SECRET_KEY to a secure random string
   ```

3. **Build and start all services**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build Docker images for all 4 services
   - Start 4 PostgreSQL databases
   - Start RabbitMQ message broker
   - Start nginx API Gateway
   - Initialize database tables automatically

4. **Verify services are running**
   ```bash
   # Check all containers are up
   docker-compose ps

   # Check service health
   curl http://localhost/api/users/health
   curl http://localhost/api/cycles/health
   curl http://localhost/api/analytics/health
   curl http://localhost/api/notifications/health
   ```

5. **Access RabbitMQ Management UI** (optional)
   - URL: `http://localhost:15672`
   - Username: `guest`
   - Password: `guest`

### Stopping the System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

---

## API Documentation

All API requests go through the **nginx gateway** on **port 80**.

### Authentication Flow

#### 1. Register a New User

```bash
POST http://localhost/api/users/register

Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "securepassword123",
  "first_name": "Jane",
  "last_name": "Doe"
}

Response: 201 Created
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser",
    ...
  }
}
```

#### 2. Login and Get JWT Token

```bash
POST http://localhost/api/users/login

Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: 200 OK
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

**Use this token in all subsequent requests:**
```
Authorization: Bearer <token>
```

---

### User Service API (Port 5001)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/users/health` | GET | No | Health check |
| `/api/users/register` | POST | No | Register new user |
| `/api/users/login` | POST | No | Login and get token |
| `/api/users/profile` | GET | Yes | Get user profile |
| `/api/users/profile` | PUT | Yes | Update profile |

---

### Cycle Tracking Service API (Port 5002)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/cycles/health` | GET | No | Health check |
| `/api/cycles/cycles` | POST | Yes | Log new cycle |
| `/api/cycles/cycles` | GET | Yes | Get user's cycles |
| `/api/cycles/cycles/<id>` | GET | Yes | Get specific cycle |
| `/api/cycles/cycles/<id>` | PUT | Yes | Update cycle |
| `/api/cycles/symptoms` | POST | Yes | Log symptom |
| `/api/cycles/symptoms` | GET | Yes | Get symptoms |

**Example: Log New Cycle**
```bash
POST http://localhost/api/cycles/cycles

Authorization: Bearer <token>
Content-Type: application/json

{
  "start_date": "2025-01-15",
  "end_date": "2025-01-20"
}
```

**Example: Log Symptom**
```bash
POST http://localhost/api/cycles/symptoms

Authorization: Bearer <token>
Content-Type: application/json

{
  "cycle_id": 1,
  "date": "2025-01-16",
  "symptom_type": "mood",
  "value": "happy",
  "severity": 2,
  "notes": "Feeling great today"
}
```

---

### Analytics Service API (Port 5003)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/analytics/health` | GET | No | Health check |
| `/api/analytics/predictions` | GET | Yes | Get predictions |
| `/api/analytics/predictions/generate` | POST | Yes | Manually generate prediction |
| `/api/analytics/insights` | GET | Yes | Get health insights |
| `/api/analytics/analytics` | GET | Yes | Get cycle analytics |

**Example: Get Insights**
```bash
GET http://localhost/api/analytics/insights

Authorization: Bearer <token>

Response:
{
  "insights": [
    {
      "type": "positive",
      "message": "Your average cycle length is 28.5 days, within normal range."
    },
    {
      "type": "positive",
      "message": "Your cycles are very regular, making predictions more accurate."
    }
  ],
  "statistics": {
    "total_cycles_tracked": 6,
    "average_cycle_length": 28.5,
    "average_period_length": 5.2,
    "cycle_regularity": "very_regular"
  }
}
```

---

### Notification Service API (Port 5004)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/notifications/health` | GET | No | Health check |
| `/api/notifications/preferences` | GET | Yes | Get notification preferences |
| `/api/notifications/preferences` | PUT | Yes | Update preferences |
| `/api/notifications/notifications` | GET | Yes | Get notifications |
| `/api/notifications/notifications/<id>` | GET | Yes | Get specific notification |

**Example: Update Notification Preferences**
```bash
PUT http://localhost/api/notifications/preferences

Authorization: Bearer <token>
Content-Type: application/json

{
  "period_reminder_enabled": true,
  "reminder_days_before": 3,
  "email_enabled": true
}
```

---

## Testing the System

### End-to-End Test Flow

1. **Register a user**
   ```bash
   curl -X POST http://localhost/api/users/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","username":"testuser","password":"pass123"}'
   ```

2. **Login and save token**
   ```bash
   TOKEN=$(curl -X POST http://localhost/api/users/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"pass123"}' \
     | jq -r '.token')
   ```

3. **Log multiple cycles** (for predictions)
   ```bash
   # Cycle 1
   curl -X POST http://localhost/api/cycles/cycles \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2024-11-15","end_date":"2024-11-20"}'

   # Cycle 2
   curl -X POST http://localhost/api/cycles/cycles \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2024-12-13","end_date":"2024-12-18"}'

   # Cycle 3
   curl -X POST http://localhost/api/cycles/cycles \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2025-01-10","end_date":"2025-01-15"}'
   ```

4. **Check analytics automatically processed**
   ```bash
   curl -X GET http://localhost/api/analytics/analytics \
     -H "Authorization: Bearer $TOKEN"
   ```

5. **Get predictions**
   ```bash
   curl -X GET http://localhost/api/analytics/predictions \
     -H "Authorization: Bearer $TOKEN"
   ```

6. **Check notifications created**
   ```bash
   curl -X GET http://localhost/api/notifications/notifications \
     -H "Authorization: Bearer $TOKEN"
   ```

### Monitoring Message Queue

1. Open RabbitMQ Management UI: `http://localhost:15672`
2. Navigate to **Queues** tab
3. Observe:
   - `analytics_cycle_queue` - Receives cycle events
   - `notification_prediction_queue` - Receives prediction events

---

## Microservices Analysis

### Advantages Demonstrated

✅ **Independent Scalability**
- Each service can scale independently based on load
- Analytics service can have more instances during heavy computation

✅ **Technology Diversity**
- Each service could use different Python versions
- Could swap PostgreSQL for MongoDB in specific services
- Different frameworks per service (Flask, FastAPI, Django)

✅ **Fault Isolation**
- If Analytics Service crashes, users can still log cycles
- Service failures don't cascade to entire system

✅ **Independent Deployment**
- Deploy Notification Service without touching other services
- Zero-downtime deployments possible per service

✅ **Team Autonomy**
- Different teams can own different services
- Parallel development without conflicts

✅ **Data Isolation**
- Each service owns its data
- No accidental data coupling

### Challenges Demonstrated

❌ **Increased Complexity**
- 4 services + 4 databases + message queue + gateway
- More moving parts to manage

❌ **Distributed Transactions**
- No ACID transactions across services
- Eventual consistency model required

❌ **Network Latency**
- Inter-service communication over network
- Multiple network hops for operations

❌ **Data Consistency**
- Analytics Service maintains copy of cycle data
- Data synchronization via events

❌ **Testing Complexity**
- Integration tests require all services running
- More complex test environments

❌ **Operational Overhead**
- More containers to monitor
- More logs to aggregate
- More complex debugging

---

## Research Notes

### Comparison Points for Thesis

| Aspect | Microservices (This Implementation) | Modular Monolith |
|--------|-------------------------------------|------------------|
| **Deployment** | Independent per service | Single deployment unit |
| **Scaling** | Scale services individually | Scale entire application |
| **Data Management** | Database per service | Shared database |
| **Communication** | REST + Message Queue | Direct function calls |
| **Fault Isolation** | High (service boundaries) | Low (shared process) |
| **Development Complexity** | High | Medium |
| **Operational Complexity** | High | Low |
| **Team Independence** | High | Medium |
| **Technology Flexibility** | High | Low |
| **Testing Complexity** | High | Medium |

### Key Observations

1. **Event-Driven Architecture** adds resilience but complexity
2. **Database-per-Service** provides isolation but makes queries harder
3. **API Gateway** simplifies client but adds single point of failure
4. **Service Independence** enables autonomy but requires coordination
5. **Message Queue** enables async communication but adds operational burden

---

## License

This project is created for academic research purposes.

---

## Author

Created for Master's research on comparing Modular Monolith vs Microservices architectures.

**Date:** 2025

**Purpose:** Academic Research
