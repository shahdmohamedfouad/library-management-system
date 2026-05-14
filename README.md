#  Library Management System API

##  Backend Development with FastAPI

---

##  Project Description

This project is a **Library Management System backend API** built using FastAPI.

It provides functionality for managing books, user authentication, borrowing system, and tracking borrowing history with secure role-based access control.

The project follows a clean, modular architecture using routers, services, models, and schemas.

---

##  Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- Redis (Caching)
- Pytest (Testing)
- Uvicorn

---

app/
│
├── core/               # Configurations, DB, Security
├── models/             # Database models (User, Book, BorrowRecord)
├── schemas/            # Pydantic schemas
├── routers/            # API endpoints
├── services/           # Business logic layer
├── utils/              # Logging, caching, helpers
├── tests/              # Unit & integration tests
│
├── main.py             # Application entry point



---

##  Project Structure

##  Features

###  Book Management (CRUD)
- Create book (Admin only)
- Get all books
- Get book by ID
- Update book
- Delete book (Admin only)

---

###  User Authentication
- User registration
- User login
- JWT token generation
- Token validation

---

###  Role-Based Authorization
- Admin (Librarian)
- Member (User)
- Protected endpoints based on roles

---

###  Borrow System
- Borrow books
- Return books
- Validate book availability
- Prevent borrowing unavailable books
- Limit number of borrowed books per user
- Track borrowing history

---

##  Redis Caching

- Cache frequently accessed data (GET all books / GET by ID)
- Cache-Aside Pattern implemented
- Cache invalidation on:
  - Create
  - Update
  - Delete

---

##  Logging & Monitoring

### Logging Features:
- API request & response logging
- Authentication logs
- Error logging
- Database operation logs

### Log Levels:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

---

###  Monitoring Dashboard (Optional)

Can be implemented using:
- Prometheus + Grafana
- ELK Stack
- Custom FastAPI dashboard

---

##  Testing

Implemented using pytest + FastAPI TestClient

### Covered:
- Authentication tests
- Authorization tests
- CRUD operations
- Borrow system logic
- Edge cases & validation

Run tests:

```bash
pytest


