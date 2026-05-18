from sqlalchemy import Column, Integer, String
from database import Base


class PostalCode(Base):
    __tablename__ = "postal_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    voivodeship = Column(String(50), nullable=True)