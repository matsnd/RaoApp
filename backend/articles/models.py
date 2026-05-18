from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.mysql import JSON
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
    # RAO-P1-017: kategoryzacja hierarchiczna (snapshot nazw) + flaga archiwalna + atrybuty
    category_main = Column(String(100), nullable=True)
    category_sub1 = Column(String(100), nullable=True)
    category_sub2 = Column(String(100), nullable=True)
    category_sub3 = Column(String(100), nullable=True)
    is_archival = Column(Boolean, nullable=False, default=False, server_default="0")
    technical_attributes = Column(JSON, nullable=True)
    # RAO-P2-012: integracja Fakturownia — 1:N globalny mapping produktu FA → artykułów RAO
    fakturownia_product_id = Column(BigInteger, nullable=True,
                                    comment="ID produktu w Fakturownia (mapping globalny 1:N)")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_art_name", "name"),
        Index("idx_art_category", "category_id"),
        Index("idx_art_owner", "owner_id"),
        Index("idx_art_registration", "registration_no"),
        Index("idx_articles_category_main", "category_main"),
        Index("idx_articles_archival", "is_archival"),
        Index("idx_articles_fakturownia_product", "fakturownia_product_id"),
    )
