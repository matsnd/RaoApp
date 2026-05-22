from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class ArticleReservation(Base):
    __tablename__ = "article_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reserved_from = Column(Date, nullable=False)
    reserved_to = Column(Date, nullable=False)
    note = Column(String(300), nullable=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
