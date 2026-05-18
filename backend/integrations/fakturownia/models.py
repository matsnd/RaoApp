"""
RAO-P2-012: Modele DB dla integracji Fakturownia.

Tabela fakturownia_settings — singleton (id=1) konfiguracji integracji:
- API token szyfrowany Fernet (api_token_ciphertext VARBINARY)
- preview tokena (api_token_preview, np. "tk_****1234") — bezpieczny do wyświetlenia
- domain_subdomain — subdomena Fakturownia (np. "toolsmart" → toolsmart.fakturownia.pl)
- audit: kto i kiedy zaktualizował token (api_token_updated_at/by)

Mapping produktów Fakturownia → artykuły RAO realizowany w `articles.fakturownia_product_id`
(1:N globalny w artykułach, decyzja architektoniczna z 2026-05-18).
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
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
