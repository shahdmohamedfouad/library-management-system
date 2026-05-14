

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrow_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="borrowed", nullable=False)  # borrowed / returned

    
    user = relationship("User", back_populates="borrow_records")
    book = relationship("Book", back_populates="borrow_records")

    def __repr__(self):
        return f"<BorrowRecord user={self.user_id} book={self.book_id}>"
