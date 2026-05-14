# app/models/book.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)
    available = Column(Boolean, default=True, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    # Relationship to borrow records
    borrow_records = relationship("BorrowRecord", back_populates="book")

    def __repr__(self):
        return f"<Book {self.title}>"

