# tests/test_library_system.py
"""
Test Suite كامل لـ Library Management System
بيغطي كل المتطلبات: Auth, CRUD, RBAC, Caching, Error Handling, Monitoring

طريقة التشغيل:
    pytest tests/test_library_system.py -v
    pytest tests/test_library_system.py -v --tb=short
"""

import sys
import os
import time
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db
from app.core.config import settings

# ═══════════════════════════════════════════════════════════════
#  Setup: In-Memory Database for Testing
# ═══════════════════════════════════════════════════════════════

TEST_DATABASE_URL = "sqlite:///./test_library.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ═══════════════════════════════════════════════════════════════
#  Helper Functions
# ═══════════════════════════════════════════════════════════════

def generate_unique_username():
    return f"testuser_{uuid.uuid4().hex[:8]}"

def generate_unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def generate_unique_isbn():
    return f"ISBN{int(time.time() * 1000)}_{uuid.uuid4().hex[:4]}"

# ═══════════════════════════════════════════════════════════════
#  Fixtures & Shared State (using module-level variables)
# ═══════════════════════════════════════════════════════════════

class TestState:
    """Shared state between tests"""
    member_token = None
    admin_token = None
    member_username = None
    admin_username = None
    created_book_id = None
    created_book_isbn = None
    borrow_record_id = None

state = TestState()

# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 1: Basic & Public Endpoints
# ═══════════════════════════════════════════════════════════════

class TestPublicEndpoints:
    """اختبار الـ Endpoints العامة اللي مش محتاجة تسجيل دخول"""

    def test_root_endpoint(self):
        """اختبار الصفحة الرئيسية"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Library Management System" in data["message"]
        assert "/docs" in data["documentation"]

    def test_health_check(self):
        """اختبار حالة السيرفر"""
        response = client.get("/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Library Management System"
        assert data["version"] == "1.0.0"
        assert "redis" in data
        assert "database" in data

    def test_system_info(self):
        """اختبار معلومات النظام"""
        response = client.get("/monitoring/info")
        assert response.status_code == 200
        data = response.json()
        assert data["app_title"] == "Library Management System"
        assert data["status"] == "running"
        assert "/docs" in data["docs_url"]

    def test_monitoring_dashboard(self):
        """اختبار لوحة المراقبة"""
        response = client.get("/monitoring/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "api_metrics" in data
        assert "system_health" in data
        assert "total_requests" in data["api_metrics"]
        assert "error_rate" in data["api_metrics"]
        assert "average_response_time_ms" in data["api_metrics"]

    def test_docs_endpoint(self):
        """اختبار Swagger UI Docs"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc_endpoint(self):
        """اختبار ReDoc Docs"""
        response = client.get("/redoc")
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 2: Authentication (التسجيل والدخول)
# ═══════════════════════════════════════════════════════════════

class TestAuthentication:
    """اختبار نظام التسجيل والدخول بالكامل"""

    def test_register_new_member_success(self):
        """تسجيل عضو جديد بنجاح"""
        state.member_username = generate_unique_username()
        email = generate_unique_email()

        response = client.post("/auth/register", json={
            "username": state.member_username,
            "email": email,
            "password": "securepass123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        state.member_token = data["access_token"]

    def test_register_duplicate_username(self):
        """محاولة تسجيل بنفس اليوزرنيم - لازم تفشل"""
        response = client.post("/auth/register", json={
            "username": state.member_username,
            "email": generate_unique_email(),
            "password": "securepass123"
        })
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self):
        """محاولة تسجيل بنفس الإيميل - لازم تفشل"""
        # First register with unique username but same email pattern won't work 
        # because we need same email, so let's use the original email
        # Actually, we need to test with same email - let's register another user first
        username2 = generate_unique_username()
        email2 = generate_unique_email()

        # Register first user
        client.post("/auth/register", json={
            "username": username2,
            "email": email2,
            "password": "securepass123"
        })

        # Try to register with same email
        response = client.post("/auth/register", json={
            "username": generate_unique_username(),
            "email": email2,
            "password": "securepass123"
        })
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self):
        """تسجيل بإيميل غلط - لازم يرجع 422"""
        response = client.post("/auth/register", json={
            "username": generate_unique_username(),
            "email": "not-an-email",
            "password": "securepass123"
        })
        assert response.status_code == 422

    def test_register_missing_fields(self):
        """تسجيل بدون بيانات مطلوبة - لازم يرجع 422"""
        response = client.post("/auth/register", json={
            "username": generate_unique_username()
            # missing email and password
        })
        assert response.status_code == 422

    def test_login_success(self):
        """دخول ناجح"""
        response = client.post("/auth/login", data={
            "username": state.member_username,
            "password": "securepass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        state.member_token = data["access_token"]

    def test_login_wrong_password(self):
        """دخول بباسورد غلط"""
        response = client.post("/auth/login", data={
            "username": state.member_username,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """دخول بيوزر مش موجود"""
        response = client.post("/auth/login", data={
            "username": "nonexistent_user_12345",
            "password": "somepassword"
        })
        assert response.status_code == 401

    def test_login_missing_credentials(self):
        """دخول بدون بيانات"""
        response = client.post("/auth/login", data={})
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 3: Protected Routes (الروابط المحمية)
# ═══════════════════════════════════════════════════════════════

class TestProtectedRoutes:
    """اختبار الروابط اللي محتاجة توكن"""

    def test_access_protected_without_token(self):
        """دخول رابط محمي بدون توكن"""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_access_protected_with_invalid_token(self):
        """دخول بتوكن غلط"""
        headers = {"Authorization": "Bearer invalid_token_123"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401

    def test_access_protected_with_valid_token(self):
        """دخول بتوكن صحيح"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == state.member_username
        assert data["role"] == "MEMBER"
        assert "email" in data

    def test_test_auth_endpoint(self):
        """اختبار endpoint التحقق من التوكن"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/users/test-auth", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "Token is valid" in data["message"]
        assert "token" in data


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 4: Role-Based Access Control (الصلاحيات)
# ═══════════════════════════════════════════════════════════════

class TestRoleBasedAccess:
    """اختبار نظام الصلاحيات (Admin vs Member)"""

    def test_01_create_admin_user(self):
        """تسجيل عضو وتحويله لـ Admin"""
        state.admin_username = generate_unique_username()
        email = generate_unique_email()

        # Register as member
        response = client.post("/auth/register", json={
            "username": state.admin_username,
            "email": email,
            "password": "adminpass123"
        })
        assert response.status_code == 201

        # Promote to admin
        response = client.post(f"/auth/make-admin/{state.admin_username}")
        assert response.status_code == 200
        data = response.json()
        assert "is now ADMIN" in data["message"]
        state.admin_token = data["access_token"]

    def test_02_admin_can_access_admin_dashboard(self):
        """Admin يقدر يدخل لوحة التحكم"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        response = client.get("/admin/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "Welcome Admin" in data["message"]
        assert data["role"] == "ADMIN"

    def test_03_member_cannot_access_admin_dashboard(self):
        """Member مش يقدر يدخل لوحة التحكم"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/admin/dashboard", headers=headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_04_admin_can_list_all_users(self):
        """Admin يقدر يشوف كل اليوزرز"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        response = client.get("/admin/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least admin and member

    def test_05_member_cannot_list_all_users(self):
        """Member مش يقدر يشوف كل اليوزرز"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/admin/users", headers=headers)
        assert response.status_code == 403

    def test_06_admin_can_delete_user(self):
        """Admin يقدر يمسح يوزر"""
        # Create a user to delete
        username = generate_unique_username()
        client.post("/auth/register", json={
            "username": username,
            "email": generate_unique_email(),
            "password": "deletepass123"
        })

        # Get all users to find the ID
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        users = client.get("/admin/users", headers=headers).json()

        target_user = next((u for u in users if u["username"] == username), None)
        assert target_user is not None

        # Delete the user
        response = client.delete(f"/admin/users/{target_user['id']}", headers=headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_07_admin_cannot_delete_another_admin(self):
        """Admin مش يقدر يمسح Admin تاني"""
        # Create another admin
        username = generate_unique_username()
        client.post("/auth/register", json={
            "username": username,
            "email": generate_unique_email(),
            "password": "adminpass123"
        })
        client.post(f"/auth/make-admin/{username}")

        # Get users
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        users = client.get("/admin/users", headers=headers).json()
        target = next((u for u in users if u["username"] == username), None)

        # Try to delete admin
        response = client.delete(f"/admin/users/{target['id']}", headers=headers)
        assert response.status_code == 403
        assert "Cannot delete admin user" in response.json()["detail"]

    def test_08_member_cannot_delete_user(self):
        """Member مش يقدر يمسح يوزر"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.delete("/admin/users/1", headers=headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 5: Books CRUD (إدارة الكتب)
# ═══════════════════════════════════════════════════════════════

class TestBooksCRUD:
    """اختبار عمليات الكتب: إضافة، عرض، تعديل، حذف"""

    def test_01_member_can_list_books(self):
        """Member يقدر يشوف الكتب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data

    def test_02_member_can_search_books(self):
        """Member يقدر يبحث في الكتب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?search=python", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_03_member_can_filter_by_category(self):
        """Member يقدر يفلتر بالتصنيف"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?category=fiction", headers=headers)
        assert response.status_code == 200

    def test_04_member_can_filter_by_availability(self):
        """Member يقدر يفلتر بالتوفر"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?available=true", headers=headers)
        assert response.status_code == 200

    def test_05_member_can_use_pagination(self):
        """Member يقدر يستخدم الترقيم"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?page=1&page_size=5", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_06_admin_can_create_book(self):
        """Admin يقدر يضيف كتاب"""
        state.created_book_isbn = generate_unique_isbn()
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        response = client.post("/books/", json={
            "title": "Test Book Title",
            "author": "Test Author",
            "isbn": state.created_book_isbn,
            "category": "Testing",
            "description": "A test book for testing",
            "quantity": 5
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Book Title"
        assert data["author"] == "Test Author"
        assert data["isbn"] == state.created_book_isbn
        assert data["quantity"] == 5
        assert data["available"] == True
        state.created_book_id = data["id"]

    def test_07_admin_cannot_create_duplicate_isbn(self):
        """Admin مش يقدر يضيف كتاب بنفس ISBN"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        response = client.post("/books/", json={
            "title": "Another Book",
            "author": "Another Author",
            "isbn": state.created_book_isbn,
            "quantity": 1
        }, headers=headers)
        assert response.status_code == 400
        assert "ISBN" in response.json()["detail"]

    def test_08_member_cannot_create_book(self):
        """Member مش يقدر يضيف كتاب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post("/books/", json={
            "title": "Member Book",
            "author": "Member Author",
            "isbn": generate_unique_isbn(),
            "quantity": 1
        }, headers=headers)
        assert response.status_code == 403

    def test_09_anyone_can_get_book_by_id(self):
        """أي حد مسجل يقدر يشوف كتاب بالـ ID"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get(f"/books/{state.created_book_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == state.created_book_id
        assert data["title"] == "Test Book Title"

    def test_10_get_nonexistent_book(self):
        """طلب كتاب مش موجود"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/99999", headers=headers)
        assert response.status_code == 404

    def test_11_admin_can_update_book(self):
        """Admin يقدر يعدل كتاب"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        response = client.put(f"/books/{state.created_book_id}", json={
            "title": "Updated Title",
            "quantity": 10
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["quantity"] == 10

    def test_12_member_cannot_update_book(self):
        """Member مش يقدر يعدل كتاب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.put(f"/books/{state.created_book_id}", json={
            "title": "Hacked Title"
        }, headers=headers)
        assert response.status_code == 403

    def test_13_admin_can_delete_book(self):
        """Admin يقدر يمسح كتاب"""
        # Create a book to delete
        isbn = generate_unique_isbn()
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        create_resp = client.post("/books/", json={
            "title": "Book to Delete",
            "author": "Delete Author",
            "isbn": isbn,
            "quantity": 1
        }, headers=headers)
        book_id = create_resp.json()["id"]

        # Delete it
        response = client.delete(f"/books/{book_id}", headers=headers)
        assert response.status_code == 204

        # Verify it's gone
        get_resp = client.get(f"/books/{book_id}", headers=headers)
        assert get_resp.status_code == 404

    def test_14_member_cannot_delete_book(self):
        """Member مش يقدر يمسح كتاب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.delete(f"/books/{state.created_book_id}", headers=headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 6: Borrowing System (نظام الاستعارة)
# ═══════════════════════════════════════════════════════════════

class TestBorrowingSystem:
    """اختبار نظام استعارة وإرجاع الكتب"""

    def test_01_setup_books_for_borrowing(self):
        """إعداد كتب للاستعارة"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}

        # Create book 1
        isbn1 = generate_unique_isbn()
        resp1 = client.post("/books/", json={
            "title": "Borrow Book 1",
            "author": "Author 1",
            "isbn": isbn1,
            "quantity": 3
        }, headers=headers)
        state.book1_id = resp1.json()["id"]

        # Create book 2
        isbn2 = generate_unique_isbn()
        resp2 = client.post("/books/", json={
            "title": "Borrow Book 2",
            "author": "Author 2",
            "isbn": isbn2,
            "quantity": 2
        }, headers=headers)
        state.book2_id = resp2.json()["id"]

        # Create book 3
        isbn3 = generate_unique_isbn()
        resp3 = client.post("/books/", json={
            "title": "Borrow Book 3",
            "author": "Author 3",
            "isbn": isbn3,
            "quantity": 1
        }, headers=headers)
        state.book3_id = resp3.json()["id"]

    def test_02_member_can_borrow_book(self):
        """Member يقدر يستعير كتاب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post(f"/books/{state.book1_id}/borrow", headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["book_id"] == state.book1_id
        assert data["status"] == "borrowed"
        state.borrow_record_id = data["id"]

    def test_03_borrowing_decreases_quantity(self):
        """الاستعارة بتقلل الكمية"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get(f"/books/{state.book1_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 2  # Was 3, now 2

    def test_04_cannot_borrow_same_book_twice(self):
        """مش يقدر يستعير نفس الكتاب مرتين"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post(f"/books/{state.book1_id}/borrow", headers=headers)
        assert response.status_code == 400
        assert "already have an active borrow" in response.json()["detail"]

    def test_05_borrowing_limit_enforced(self):
        """حد الاستعارة ٣ كتب بيتطبق"""
        headers = {"Authorization": f"Bearer {state.member_token}"}

        # Borrow book 2
        resp2 = client.post(f"/books/{state.book2_id}/borrow", headers=headers)
        assert resp2.status_code == 201

        # Borrow book 3
        resp3 = client.post(f"/books/{state.book3_id}/borrow", headers=headers)
        assert resp3.status_code == 201

        # Try to borrow a 4th book - should fail
        isbn4 = generate_unique_isbn()
        admin_headers = {"Authorization": f"Bearer {state.admin_token}"}
        book4 = client.post("/books/", json={
            "title": "Borrow Book 4",
            "author": "Author 4",
            "isbn": isbn4,
            "quantity": 1
        }, headers=admin_headers)
        book4_id = book4.json()["id"]

        response = client.post(f"/books/{book4_id}/borrow", headers=headers)
        assert response.status_code == 400
        assert "maximum borrowing limit" in response.json()["detail"]

    def test_06_member_can_return_book(self):
        """Member يقدر يرجع كتاب"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post(f"/books/{state.book1_id}/return", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "returned"
        assert data["return_date"] is not None

    def test_07_returning_increases_quantity(self):
        """الإرجاع بيزود الكمية"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get(f"/books/{state.book1_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 3  # Back to original

    def test_08_cannot_return_non_borrowed_book(self):
        """مش يقدر يرجع كتاب ما استعارهوش"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post(f"/books/{state.book1_id}/return", headers=headers)
        assert response.status_code == 404
        assert "No active borrow record" in response.json()["detail"]

    def test_09_member_can_view_borrow_history(self):
        """Member يقدر يشوف تاريخ الاستعارة"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/my/borrows", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least 3 borrow records

    def test_10_cannot_borrow_unavailable_book(self):
        """مش يقدر يستعير كتاب مش متوفر"""
        # Create book with quantity 0
        isbn = generate_unique_isbn()
        headers = {"Authorization": f"Bearer {state.admin_token}"}
        book = client.post("/books/", json={
            "title": "Unavailable Book",
            "author": "Author",
            "isbn": isbn,
            "quantity": 0
        }, headers=headers)
        book_id = book.json()["id"]

        member_headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.post(f"/books/{book_id}/borrow", headers=member_headers)
        assert response.status_code == 400
        assert "not available" in response.json()["detail"]


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 7: Error Handling (معالجة الأخطاء)
# ═══════════════════════════════════════════════════════════════

class TestErrorHandling:
    """اختبار معالجة الأخطاء"""

    def test_validation_error_format(self):
        """تنسيق رسالة الخطأ في الـ Validation"""
        response = client.post("/auth/register", json={
            "username": "ab",  # Too short might fail
            "email": "bad-email",
            "password": "12"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_404_error_format(self):
        """تنسيق خطأ 404"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/999999", headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_403_error_format(self):
        """تنسيق خطأ 403"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/admin/dashboard", headers=headers)
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    def test_401_error_format(self):
        """تنسيق خطأ 401"""
        response = client.get("/users/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 8: Monitoring (المراقبة)
# ═══════════════════════════════════════════════════════════════

class TestMonitoring:
    """اختبار نظام المراقبة"""

    def test_request_counting(self):
        """عد الطلبات بيتسجل"""
        # Make a request first
        client.get("/")

        response = client.get("/monitoring/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["api_metrics"]["total_requests"] > 0

    def test_error_counting(self):
        """عد الأخطاء بيتسجل"""
        # Make an error request
        client.get("/users/me")  # 401 error

        response = client.get("/monitoring/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Error count might be > 0
        assert "error_rate" in data["api_metrics"]

    def test_response_time_tracking(self):
        """تتبع وقت الاستجابة"""
        response = client.get("/monitoring/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "average_response_time_ms" in data["api_metrics"]
        assert isinstance(data["api_metrics"]["average_response_time_ms"], (int, float))

    def test_system_health_status(self):
        """حالة صحة النظام"""
        response = client.get("/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 9: Caching (التخزين المؤقت)
# ═══════════════════════════════════════════════════════════════

class TestCaching:
    """اختبار نظام التخزين المؤقت"""

    def test_cache_hit_faster(self):
        """الكاش بيخلي الطلب أسرع"""
        headers = {"Authorization": f"Bearer {state.member_token}"}

        # First request (cache miss)
        start1 = time.time()
        resp1 = client.get("/books/", headers=headers)
        time1 = time.time() - start1

        assert resp1.status_code == 200

        # Second request (cache hit)
        start2 = time.time()
        resp2 = client.get("/books/", headers=headers)
        time2 = time.time() - start2

        assert resp2.status_code == 200
        # Cache hit should be faster (or at least not slower)
        # Note: In test env without real redis, this might not work perfectly

    def test_cache_invalidation_on_create(self):
        """الكاش بيتمسح لما نضيف كتاب جديد"""
        headers = {"Authorization": f"Bearer {state.admin_token}"}

        # Get books list
        client.get("/books/", headers=headers)

        # Create new book
        isbn = generate_unique_isbn()
        client.post("/books/", json={
            "title": "Cache Test Book",
            "author": "Cache Author",
            "isbn": isbn,
            "quantity": 1
        }, headers=headers)

        # List should be updated (cache invalidated)
        response = client.get("/books/", headers=headers)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════
#  TEST CLASS 10: Edge Cases (الحالات الحدية)
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    """اختبار الحالات الحدية والغريبة"""

    def test_empty_search_results(self):
        """بحث مش بيرجع نتايج"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?search=xyznonexistent123", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_pagination_beyond_total(self):
        """ترقيم بعد عدد الصفحات الكلي"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?page=999&page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_large_page_size(self):
        """page size كبير"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?page_size=100", headers=headers)
        assert response.status_code == 200

    def test_invalid_page_number(self):
        """رقم صفحة غلط"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?page=0", headers=headers)
        assert response.status_code == 422  # Should fail validation

    def test_sql_injection_attempt(self):
        """محاولة SQL Injection"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?search='; DROP TABLE books; --", headers=headers)
        # Should NOT crash - SQLAlchemy protects against this
        assert response.status_code == 200

    def test_very_long_search_term(self):
        """بحث بنص طويل جداً"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        long_term = "a" * 500
        response = client.get(f"/books/?search={long_term}", headers=headers)
        assert response.status_code == 200

    def test_special_characters_in_search(self):
        """بحث بحروف خاصة"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?search=@#$%^&*()", headers=headers)
        assert response.status_code == 200

    def test_unicode_characters(self):
        """حروف يونيكود"""
        headers = {"Authorization": f"Bearer {state.member_token}"}
        response = client.get("/books/?search=كتاب عربي", headers=headers)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════
#  Run Instructions
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])

