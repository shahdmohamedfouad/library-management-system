# app/schemas/book.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─────────── Book Schemas ───────────

class BookCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: int = 1


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    available: Optional[bool] = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: Optional[str]
    category: Optional[str]
    description: Optional[str]
    available: bool
    quantity: int

    class Config:
        from_attributes = True


# ─────────── BorrowRecord Schemas ───────────

class BorrowResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime
    return_date: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ─────────── Pagination Schema ───────────

class PaginatedBooks(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    results: list[BookResponse]

