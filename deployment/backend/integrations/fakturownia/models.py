"""
RAO-P2-012 / RAO-P2-058: Modele DB dla integracji Fakturownia.

Tabela fakturownia_settings — singleton (id=1) konfiguracji integracji:
- API token szyfrowany Fernet (api_token_ciphertext VARBINARY)
- preview tokena (api_token_preview, np. "tk_****1234") — bezpieczny do wyświetlenia
- domain_subdomain — subdomena Fakturownia (np. "toolsmart" → toolsmart.fakturownia.pl)
- audit: kto i kiedy zaktualizował token (api_token_updated_at/by)

Tabela fakturownia_products_cache (RAO-P2-058 Faza 1) — lokalny cache katalogu produktów FA:
- product_id BIGINT UNIQUE — ID produktu w Fakturownia (klucz upsert)
- code, name, price_net, tax_rate, gtu_code, pkwiu — snapshot metadanych
- synced_at — kiedy rekord był ostatnio odświeżony z FA API

Mapping produktów Fakturownia → artykuły RAO realizowany w `articles.fakturownia_product_id`
(1:N globalny w artykułach, decyzja architektoniczna z 2026-05-18).
"""
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.mysql import VARBINARY

from database import Base


class FakturowniaSettings(Base):
    __tablename__ = "fakturownia_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, nullable=False, default=False, server_default="0",
                    comment="Czy integracja jest włączona")
    api_token_ciphertext = Column(VARBINARY(512), nullable=True,
                                  comment="API token zaszyfrowany Fernet (VARBINARY)")
    api_token_preview = Column(String(32), nullable=True,
                               comment="Preview tokena np. tk_****1234 (do UI)")
    domain_subdomain = Column(String(100), nullable=True,
                              comment="Subdomena Fakturownia np. toolsmart")
    api_token_updated_at = Column(DateTime, nullable=True,
                                  comment="Kiedy ostatnio zaktualizowano token")
    api_token_updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                                  nullable=True, comment="Kto zaktualizował token (FK users.id)")
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=True, onupdate=func.current_timestamp())


class FakturowniaProductCache(Base):
    """RAO-P2-058 Faza 1: lokalny cache katalogu produktów Fakturownia.

    Wypełniany przez `POST /integrations/fakturownia/sync-products` (upsert po product_id).
    Odczytywany przez `GET /integrations/fakturownia/products/search?q=...` (LIKE %q%).
    """
    __tablename__ = "fakturownia_products_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, nullable=False, unique=True,
                        comment="ID produktu w Fakturownia (klucz upsert)")
    code = Column(String(64), nullable=True, comment="Kod produktu z FA")
    name = Column(String(255), nullable=False, comment="Nazwa produktu z FA")
    price_net = Column(Numeric(12, 2), nullable=True, comment="Cena netto snapshot")
    currency = Column(String(8), nullable=True, default="PLN")
    tax_rate = Column(String(16), nullable=True, comment="Stawka VAT np. 23")
    gtu_code = Column(String(32), nullable=True, comment="GTU code z FA")
    pkwiu = Column(String(64), nullable=True, comment="PKWiU z FA")
    synced_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                       onupdate=func.current_timestamp(),
                       comment="Kiedy rekord był ostatnio odświeżony z FA API")

    __table_args__ = (
        Index("ix_fpc_name", "name"),
        Index("ix_fpc_code", "code"),
    )
