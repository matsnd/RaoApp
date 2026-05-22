"""RAO-P3-005: Model audit_log.

Centralny dziennik zmian: kto, co, kiedy, jakie dane zmienił.
old_data / new_data trzymają snapshot rekordu w JSON.
"""
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Index,
)
from sqlalchemy.sql import func

from database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_created", "created_at"),
    )
