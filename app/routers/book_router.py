# app/routers/books.py
"""
عضو 5: Protected Routes & Search
- كل الـ routes محتاجة JWT Token صالح (Member أو Admin)
- Search/Filter على الكتب
- Pagination
- Borrow / Return كتاب
- Admin: إضافة / تعديل / حذف كتاب
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime
import math
from app.core.cache import cache, invalidate_book_cache
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.borrow import BorrowRecord
from app.schemas.book import (
    BookCreate, BookUpdate, BookResponse,
    BorrowResponse, PaginatedBooks
)
from app.core.security import get_current_user
from app.dependencies.auth import get_current_active_admin


router = APIRouter()


# ══════════════════════════════════════════════
#  📚  GET /books  →  List + Search + Filter + Pagination
#  🔐 Protected: any logged-in user (Member or Admin)
# ══════════════════════════════════════════════
@router.get("/", response_model=PaginatedBooks)
@cache(ttl=60)
def get_books(
    search: Optional[str] = Query(None, description="Search by title or author"),
    category: Optional[str] = Query(None, description="Filter by category"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Book)

    if search:
        keyword = f"%{search}%"
        query = query.filter(
            or_(Book.title.ilike(keyword), Book.author.ilike(keyword))
        )

    if category:
        query = query.filter(Book.category.ilike(f"%{category}%"))

    if available is not None:
        query = query.filter(Book.available == available)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    books = query.offset(offset).limit(page_size).all()

    return PaginatedBooks(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=books
    )


# ══════════════════════════════════════════════
#  📖  GET /books/{book_id}  →  Book Details
#  🔐 Protected: any logged-in user
# ══════════════════════════════════════════════
@router.get("/{book_id}", response_model=BookResponse)
@cache(ttl=300)
def get_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with id={book_id} not found")
    return book


# ══════════════════════════════════════════════
#  ➕  POST /books  →  Add New Book
#  🔐 Admin Only
# ══════════════════════════════════════════════
@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    if book_data.isbn:
        if db.query(Book).filter(Book.isbn == book_data.isbn).first():
            raise HTTPException(status_code=400, detail="A book with this ISBN already exists")

    new_book = Book(
        title=book_data.title,
        author=book_data.author,
        isbn=book_data.isbn,
        category=book_data.category,
        description=book_data.description,
        quantity=book_data.quantity,
        available=book_data.quantity > 0
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    invalidate_book_cache(new_book.id)
    return new_book


# ══════════════════════════════════════════════
#  ✏️  PUT /books/{book_id}  →  Update Book
#  🔐 Admin Only
# ══════════════════════════════════════════════
@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for field, value in book_data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    if book_data.quantity is not None:
        book.available = book.quantity > 0

    db.commit()
    db.refresh(book)
    invalidate_book_cache(book_id)
    return book


# ══════════════════════════════════════════════
#  🗑️  DELETE /books/{book_id}  →  Delete Book
#  🔐 Admin Only
# ══════════════════════════════════════════════
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    invalidate_book_cache(book_id)


# ══════════════════════════════════════════════
#  📤  POST /books/{book_id}/borrow  →  Borrow a Book
#  🔐 Protected: Member or Admin
# ══════════════════════════════════════════════
@router.post("/{book_id}/borrow", response_model=BorrowResponse, status_code=201)
def borrow_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.available or book.quantity < 1:
        raise HTTPException(status_code=400, detail="Book is not available for borrowing")

    active_borrows = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.status == "borrowed"
    ).count()

    if active_borrows >= 3:
        raise HTTPException(
            status_code=400,
            detail="You have reached the maximum borrowing limit (3 books). Please return some books first."
        )

    # Check if user already borrowed this book
    active = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.book_id == book_id,
        BorrowRecord.status == "borrowed"
    ).first()
    if active:
        raise HTTPException(status_code=400, detail="You already have an active borrow for this book")

    # Create borrow record
    record = BorrowRecord(
        user_id=current_user.id,
        book_id=book_id,
        status="borrowed"
    )
    db.add(record)

    # Update book quantity
    book.quantity -= 1
    if book.quantity == 0:
        book.available = False

    db.commit()
    db.refresh(record)
    invalidate_book_cache(book_id)

    return record


# ══════════════════════════════════════════════
#  📥  POST /books/{book_id}/return  →  Return a Book
#  🔐 Protected: Member or Admin
# ══════════════════════════════════════════════
@router.post("/{book_id}/return", response_model=BorrowResponse)
def return_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.book_id == book_id,
        BorrowRecord.status == "borrowed"
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="No active borrow record found for this book")

    record.status = "returned"
    record.return_date = datetime.utcnow()

    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.quantity += 1
        book.available = True

    db.commit()
    db.refresh(record)
    invalidate_book_cache(book_id)
    return record


# ══════════════════════════════════════════════
#  📋  GET /books/my/borrows  →  My Borrow History
#  🔐 Protected: logged-in user
# ══════════════════════════════════════════════
@router.get("/my/borrows", response_model=list[BorrowResponse])
def get_my_borrows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(BorrowRecord).filter(BorrowRecord.user_id == current_user.id).all()

