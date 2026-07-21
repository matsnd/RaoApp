from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, Integer, Numeric, String
from database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(String(400), nullable=True)
    notes = Column(String(200), nullable=True)
    replacement_value = Column(Numeric(18, 2), nullable=True)
    fakturownia_product_id = Column(BigInteger, nullable=True)
    fakturownia_tax_rate = Column(String(10), nullable=True)
    fakturownia_gtu_code = Column(String(20), nullable=True)
    fakturownia_pkwiu = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_svc_name", "name"),
        Index("idx_services_fakturownia_product", "fakturownia_product_id"),
    )
