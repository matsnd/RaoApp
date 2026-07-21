from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import JSON
from database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
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
    # kategoryzacja hierarchiczna (snapshot nazw)
    category_main = Column(String(100), nullable=True)
    category_sub1 = Column(String(100), nullable=True)
    category_sub2 = Column(String(100), nullable=True)
    category_sub3 = Column(String(100), nullable=True)
    is_external = Column(Boolean, nullable=False, default=False, server_default="0")
    power_type = Column(String(10), nullable=False, server_default="other", default="other")
    technical_attributes = Column(JSON, nullable=True)
    reach_m = Column(Numeric(8, 2), nullable=True, comment="Zasięg w metrach")
    capacity_t = Column(Numeric(8, 2), nullable=True, comment="Udźwig w tonach")
    accessories = Column(Text, nullable=True, comment="Dodatkowe akcesoria / wyposażenie")
    # Fakturownia mapping (seed od nowa)
    fakturownia_product_id = Column(BigInteger, nullable=True)
    fakturownia_tax_rate = Column(String(10), nullable=True)
    fakturownia_gtu_code = Column(String(20), nullable=True)
    fakturownia_pkwiu = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_mach_name", "name"),
        Index("idx_mach_category", "category_id"),
        Index("idx_mach_owner", "owner_id"),
        Index("idx_mach_registration", "registration_no"),
        Index("idx_machines_category_main", "category_main"),
        Index("idx_machines_fakturownia_product", "fakturownia_product_id"),
        Index("idx_machines_reach", "reach_m"),
        Index("idx_machines_capacity", "capacity_t"),
        Index("idx_machines_external", "is_external"),
    )
