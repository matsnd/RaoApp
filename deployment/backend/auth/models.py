from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=True, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=True)
    role = Column(Enum("admin", "user", "viewer"), nullable=False, default="user")
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
