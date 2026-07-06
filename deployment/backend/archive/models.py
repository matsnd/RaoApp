"""RAO-P2-062 Faza 1 - modele SQLAlchemy dla tabel archive_*.

Mirror oryginalnych tabel (contracts/contract_positions/position_conditions/
contract_service_fees/contract_settlements/articles/categories) BEZ is_legacy.

FK do tabel wspoldzielonych (contractors, branches, salespeople, postal_codes,
rate_types) zostaja jak w oryginale. FK wewnatrz archive_* (np.
archive_contract_positions.contract_id -> archive_contracts.id) izoluja archiwum
od nowych umow.

Zasada: archiwum = READ-ONLY z wyjatkiem:
  - archive_categories (CRUD - edycja kategorii archiwum)
  - archive_articles.category_id (PATCH - przypisanie maszyny do kategorii)
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class ArchiveCategory(Base):
    __tablename__ = "archive_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    code = Column(String(40), nullable=True)
    description = Column(String(400), nullable=True)
    parent_id = Column(
        Integer,
        ForeignKey("archive_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    level = Column(
        Enum("main", "sub1", "sub2", "sub3", name="archive_category_level"),
        nullable=False,
        default="main",
        server_default="main",
    )

    parent = relationship(
        "ArchiveCategory",
        remote_side="ArchiveCategory.id",
        back_populates="children",
        lazy="selectin",
    )
    children = relationship(
        "ArchiveCategory",
        back_populates="parent",
        cascade="save-update",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_archive_categories_name", "name"),
        Index("idx_archive_categories_parent", "parent_id"),
    )


class ArchiveArticle(Base):
    __tablename__ = "archive_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_service = Column(Boolean, nullable=False, default=False)
    internal_number = Column(String(50), nullable=True)
    registration_no = Column(String(40), nullable=True)
    serial_no = Column(String(40), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    replacement_value = Column(Numeric(18, 2), nullable=True)
    category_id = Column(
        Integer,
        ForeignKey("archive_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_id = Column(Integer, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(400), nullable=True)
    notes = Column(String(200), nullable=True)
    rental_days = Column(Integer, nullable=True)
    article_type = Column(String(20), nullable=True)
    category_main = Column(String(100), nullable=True)
    category_sub1 = Column(String(100), nullable=True)
    category_sub2 = Column(String(100), nullable=True)
    category_sub3 = Column(String(100), nullable=True)
    is_archival = Column(Boolean, nullable=False, default=False, server_default="0")
    is_external = Column(Boolean, nullable=False, default=False, server_default="0")
    technical_attributes = Column(JSON, nullable=True)
    zasieg_m = Column(Numeric(8, 2), nullable=True, comment="Zasieg w metrach")
    udzwig_t = Column(Numeric(8, 2), nullable=True, comment="Udwig w tonach")
    dodatki = Column(Text, nullable=True, comment="Dodatkowe akcesoria / wyposazenie")
    fakturownia_product_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    category = relationship("ArchiveCategory", lazy="selectin")

    __table_args__ = (
        Index("idx_archive_art_name", "name"),
        Index("idx_archive_art_category", "category_id"),
        Index("idx_archive_art_owner", "owner_id"),
        Index("idx_archive_art_registration", "registration_no"),
        Index("idx_archive_articles_category_main", "category_main"),
        Index("idx_archive_articles_archival", "is_archival"),
        Index("idx_archive_articles_external", "is_external"),
    )


class ArchiveContract(Base):
    __tablename__ = "archive_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    salesperson_id = Column(Integer, ForeignKey("salespeople.id", ondelete="SET NULL"), nullable=True)
    number = Column(String(40), nullable=False, unique=True)
    oid = Column(String(40), nullable=True, comment="Numer zamowienia w Fakturownia")
    auto_number = Column(Integer, nullable=True)
    contract_type = Column(String(1), nullable=False, default="S")
    delivery_address = Column(Text, nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code_id = Column(
        Integer,
        ForeignKey("postal_codes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    prepayment_amount = Column(Numeric(18, 2), nullable=True, default=0)
    prepayment_document = Column(String(200), nullable=True)
    invoice_amount = Column(Numeric(18, 2), nullable=True, default=0)
    invoice_document = Column(String(40), nullable=True)
    notes = Column(Text, nullable=True)
    contact_person1 = Column(String(100), nullable=True)
    contact_phone1 = Column(String(100), nullable=True)
    show_person1 = Column(Boolean, nullable=False, default=True)
    contact_person2 = Column(String(100), nullable=True)
    contact_phone2 = Column(String(100), nullable=True)
    show_person2 = Column(Boolean, nullable=False, default=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(40), nullable=True)
    contractor_name = Column(String(200), nullable=True)
    print_path = Column(String(100), nullable=True)
    print_date = Column(DateTime, nullable=True)
    report_without_data = Column(Boolean, nullable=False, default=False)
    hide_delivery_address = Column(Boolean, nullable=False, default=False)
    signatures_on_page1 = Column(Boolean, nullable=False, default=False)
    working_days_per_week = Column(Integer, nullable=True, default=6)
    position_count = Column(Integer, nullable=True, default=0)
    is_settled = Column(Boolean, nullable=False, default=False)
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    positions = relationship(
        "ArchiveContractPosition",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    service_fees = relationship(
        "ArchiveContractServiceFee",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    settlements = relationship(
        "ArchiveContractSettlement",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ArchiveContractPosition(Base):
    __tablename__ = "archive_contract_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(
        Integer,
        ForeignKey("archive_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id = Column(
        Integer,
        ForeignKey("archive_articles.id"),
        nullable=False,
    )
    rental_type = Column(String(20), nullable=True)
    description = Column(String(400), nullable=True)
    rental_days = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True, default=1)
    unit_price = Column(Numeric(18, 2), nullable=True)
    costs = Column(Numeric(18, 2), nullable=True, default=0)
    rate_type_id = Column(Integer, ForeignKey("rate_types.id", ondelete="SET NULL"), nullable=True)
    billing_frequency = Column(String(20), nullable=True)
    billing_unit = Column(String(20), nullable=True)
    supplier_id = Column(Integer, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(Date, nullable=True)
    article_name = Column(String(400), nullable=True)

    contract = relationship("ArchiveContract", back_populates="positions")
    conditions = relationship(
        "ArchivePositionCondition",
        back_populates="position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    article = relationship("ArchiveArticle", lazy="selectin")


class ArchivePositionCondition(Base):
    __tablename__ = "archive_position_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(
        Integer,
        ForeignKey("archive_contract_positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rate_type_id = Column(Integer, ForeignKey("rate_types.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(400), nullable=True)
    rate1 = Column(Numeric(18, 2), nullable=True)
    rate2 = Column(Numeric(18, 2), nullable=True)
    billing_label = Column(String(20), nullable=True)
    period_count = Column(Integer, nullable=True)
    minimum = Column(Integer, nullable=True)

    position = relationship("ArchiveContractPosition", back_populates="conditions")


class ArchiveContractServiceFee(Base):
    __tablename__ = "archive_contract_service_fees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(
        Integer,
        ForeignKey("archive_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order = Column(Integer, nullable=False, default=0)
    name = Column(String(200), nullable=False)
    amount_from = Column(Numeric(18, 2), nullable=True)
    amount_to = Column(Numeric(18, 2), nullable=True)
    unit = Column(String(50), nullable=True)
    description = Column(String(400), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    article_id = Column(Integer, nullable=True)
    default_price = Column(Numeric(18, 2), nullable=True)

    contract = relationship("ArchiveContract", back_populates="service_fees")


class ArchiveContractSettlement(Base):
    __tablename__ = "archive_contract_settlements"
    __table_args__ = (
        UniqueConstraint(
            "contract_id",
            "position_id",
            "service_fee_id",
            "settled_at",
            name="uq_archive_settlements_contract_pos_fee_date",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(
        Integer,
        ForeignKey("archive_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id = Column(
        Integer,
        ForeignKey("archive_contract_positions.id", ondelete="CASCADE"),
        nullable=True,
    )
    service_fee_id = Column(
        Integer,
        ForeignKey("archive_contract_service_fees.id", ondelete="CASCADE"),
        nullable=True,
    )
    cost_client = Column(Numeric(18, 2), nullable=True)
    cost_company = Column(Numeric(18, 2), nullable=True)
    notes = Column(Text, nullable=True)
    settled_at = Column(Date, nullable=True, comment="Data rozliczenia")
    source = Column(String(20), nullable=True, server_default="manual",
                    comment="Zrodlo: legacy/fakturownia/manual")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    contract = relationship("ArchiveContract", back_populates="settlements", lazy="selectin")
    position = relationship("ArchiveContractPosition", lazy="selectin")
    service_fee = relationship("ArchiveContractServiceFee", lazy="selectin")

    @property
    def margin(self):
        if self.cost_client is None or self.cost_company is None:
            return None
        return self.cost_client - self.cost_company
