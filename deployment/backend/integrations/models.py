from sqlalchemy import Column, Integer, String
from database import Base


class PostalCode(Base):
    __tablename__ = "postal_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    postal_code = Column(String(10), nullable=False, unique=True, index=True)
    city = Column(String(100), nullable=False)
    wojewodztwo = Column(String(50), nullable=True)
    powiat = Column(String(100), nullable=True)
    gmina = Column(String(100), nullable=True)