from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_service = Column(Boolean, nullable=False, default=False)
    internal_number = Column(String(50), nullable=True)
    registration_no = Column(String(40), nullable=True)
    serial_no = Column(String(40), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    replacement_value = Column(Numeric(18, 2), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    owner_id = Column(Integer, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(400), nullable=True)
    notes = Column(String(200), nullable=True)
    rental_days = Column(Integer, nullable=True)
    article_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
