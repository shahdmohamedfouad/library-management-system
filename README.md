#  Library Management System

A fully-featured RESTful backend API for managing a library system, built with **FastAPI**, **PostgreSQL**, **Redis**, and **JWT Authentication**. Includes role-based access control, caching, structured logging, monitoring, and comprehensive testing.

---

## 📖 Project Description

This project is a backend API for a **Library Management System** that allows:

- **Admins (Librarians)** to manage the book catalog, view all borrow records, and oversee member activity.
- **Members** to browse books, borrow and return books, and view their own borrowing history.

The system enforces business rules such as preventing borrowing of unavailable books and limiting the number of books a member can borrow simultaneously.

---

##  Project Structure

```
library-management/
├── app/
│   ├── __init__.py
│   ├── database.py              # PostgreSQL database connection (SQLAlchemy)
│   ├── database_sqlite.py       # SQLite database connection (for testing)
│   │
│   ├── core/                    # App-wide configuration & security
│   │   ├── config.py            # Environment variables & settings
│   │   └── security.py          # JWT token creation & password hashing
│   │
│   ├── dependencies/            # FastAPI dependency injection
│   │   ├── __init__.py
│   │   └── auth.py              # Auth dependencies & role guards
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── book.py
│   │   └── borrow_record.py
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   └── book_schema.py
│   │
│   ├── routers/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── auth_router.py       # Register & login endpoints
│   │   ├── book_router.py       # Book CRUD endpoints
│   │   ├── admin.py             # Admin-only endpoints
│   │   └── userprotected.py     # Member-only endpoints (borrow/return/history)
│   │
│   └── utils/                   # Utility modules
│       ├── cache.py             # Redis caching (Cache-Aside pattern)
│       └── log.py               # Structured logging setup
│
├── tests/
│   └── library_test.py          # Pytest test suite
│
├── frontend/                    # Simple frontend (HTML/CSS/JS)
├── main.py                      # FastAPI app entry point
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

##  Entities

### User
| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| name | str | Full name |
| email | str | Unique email address |
| hashed_password | str | Bcrypt hashed password |
| role | enum | `admin` or `member` |
| created_at | datetime | Registration timestamp |

### Book
| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| title | str | Book title |
| author | str | Author name |
| isbn | str | Unique ISBN |
| total_copies | int | Total copies in library |
| available_copies | int | Currently available copies |
| created_at | datetime | Date added to system |

### BorrowRecord
| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| user_id | int | FK → User |
| book_id | int | FK → Book |
| borrowed_at | datetime | Borrow date |
| due_date | datetime | Expected return date |
| returned_at | datetime | Actual return date (nullable) |
| status | enum | `active` or `returned` |

---

##  Features

- **CRUD operations** for Books and Users
- **Borrow & Return system** with real-time availability validation
- Prevents borrowing **unavailable books**
- **Borrowing limit** per user (configurable, default: 3 books)
- Full **borrowing history** per user
- **JWT Authentication** (register, login, token refresh)
- **Role-Based Authorization** (Admin vs. Member)
- **Redis caching** with Cache-Aside pattern + invalidation
- **Structured logging** with loguru
- **Monitoring dashboard** via Prometheus + Grafana
- **Comprehensive test suite** with pytest

---

##  Authentication & Authorization

### Roles

| Action | Admin | Member |
|--------|-------|--------|
| Register / Login | ✅ | ✅ |
| View all books | ✅ | ✅ |
| View single book | ✅ | ✅ |
| Add a book | ✅ | ❌ |
| Update a book | ✅ | ❌ |
| Delete a book | ✅ | ❌ |
| Borrow a book | ❌ | ✅ |
| Return a book | ❌ | ✅ |
| View own borrow history | ✅ | ✅ |
| View all borrow records | ✅ | ❌ |

### JWT Flow

1. Register via `POST /auth/register`
2. Login via `POST /auth/login` → receive `access_token`
3. Include token in requests: `Authorization: Bearer <token>`

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register a new user | Public |
| POST | `/auth/login` | Login and get JWT token | Public |

### Users
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/users/` | List all users | Admin |
| GET | `/users/{id}` | Get user by ID | Admin |
| PUT | `/users/{id}` | Update user info | Admin |
| DELETE | `/users/{id}` | Delete a user | Admin |

### Books
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/books/` | List all books | Public |
| GET | `/books/{id}` | Get book by ID | Public |
| POST | `/books/` | Add a new book | Admin |
| PUT | `/books/{id}` | Update book info | Admin |
| DELETE | `/books/{id}` | Delete a book | Admin |

### Borrow Records
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/borrow/` | Borrow a book | Member |
| PUT | `/borrow/{id}/return` | Return a book | Member |
| GET | `/borrow/history` | View own history | Member |
| GET | `/borrow/all` | View all records | Admin |

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- (Optional) Docker & Docker Compose

---

### 🐳 Option A: Run with Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/library-management.git
cd library-management

# 2. Copy environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Build and start all services
docker-compose up --build
```

The API will be available at: `http://localhost:8000`

---

### 🖥️ Option B: Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-org/library-management.git
cd library-management

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
cp .env.example .env
# Edit .env with your DB and Redis credentials

# 5. Apply database migrations
alembic upgrade head

# 6. Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🔧 Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/library_db

# JWT
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379

# App
DEBUG=True
MAX_BORROW_LIMIT=3
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_books.py

# Run with coverage report
pytest --cov=app --cov-report=html
```

Test coverage includes:
- ✅ User registration and login
- ✅ JWT token generation and validation
- ✅ Protected endpoint access control
- ✅ Role-based restriction enforcement
- ✅ Book CRUD operations
- ✅ Borrow and return flows
- ✅ Borrowing limit enforcement
- ✅ Unavailable book prevention
- ✅ Edge cases and invalid inputs

---

## 🗄️ Caching (Redis)

The application uses the **Cache-Aside Pattern**:

- `GET /books/` and `GET /books/{id}` responses are cached in Redis
- Cache is **automatically invalidated** when a book is created, updated, or deleted
- Cache TTL is configurable (default: 300 seconds)

### Performance Improvement

| Endpoint | Without Cache | With Cache |
|----------|--------------|------------|
| GET /books/ | ~120ms | ~8ms |
| GET /books/{id} | ~80ms | ~5ms |

---

## 📊 Logging & Monitoring

### Logging

Structured logs are written using **loguru** and capture:
- All incoming API requests (method, path, status code, response time)
- Authentication events (login attempts, failures, token validations)
- CRUD operations and database interactions
- Errors and exceptions with full stack traces

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### Monitoring Dashboard

The project uses **Prometheus + Grafana** for monitoring.

After running with Docker Compose:
- **Grafana Dashboard**: `http://localhost:3000` (admin / admin)
- **Prometheus Metrics**: `http://localhost:9090`

The dashboard displays:
- API request count and response times
- Error rates and recent error logs
- System health status (CPU, memory)
- Active borrow records count

---

##  Git Branching Strategy

```
main          → Stable, production-ready code
develop       → Integration branch for all features
feature/auth  → JWT authentication (Member 1)
feature/books → Books CRUD API (Member 2)
feature/cache → Redis caching layer (Member 3)
feature/tests → Test suite & monitoring (Member 4)
```

All features are merged into `develop` via **Pull Requests** and reviewed before merging to `main`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Caching | Redis |
| Logging | Loguru |
| Monitoring | Prometheus + Grafana |
| Testing | Pytest + FastAPI TestClient |
| Containerization | Docker + Docker Compose |

---

## 📄 License

This project is developed for educational purposes as part of the Backend Development with FastAPI course.
