"""
RAO-P2-012: Pydantic v2 schemas for Fakturownia integration.

Security: extra='forbid' on all input schemas to reject unexpected fields.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Settings ──────────────────────────────────────────────────────────────────

class FakturowniaSettingsIn(BaseModel):
    """Input: create or update Fakturownia integration settings (admin only).

    SECURITY:
    - api_token is plaintext here; service layer encrypts it with Fernet before DB storage.
    - domain_subdomain validated against ^[a-z0-9-]+$ (SSRF guard at schema level).
    """
    model_config = {"extra": "forbid"}

    enabled: bool = False
    api_token: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description=(
            "Plaintext Fakturownia API token "
            "(encrypted before DB storage, never returned in responses)"
        ),
    )
    domain_subdomain: Optional[str] = Field(
        None,
        pattern=r"^[a-z0-9-]+$",
        max_length=100,
        description="Subdomain only, e.g. 'toolsmart' → toolsmart.fakturownia.pl",
    )


class FakturowniaSettingsOut(BaseModel):
    """Output: Fakturownia settings.

    SECURITY: api_token is NEVER returned — only api_token_preview (masked, e.g. 'tk_****9876').
    """
    model_config = {"from_attributes": True, "extra": "forbid"}

    id: int
    enabled: bool
    api_token_preview: Optional[str] = None
    domain_subdomain: Optional[str] = None
    api_token_updated_at: Optional[datetime] = None
    api_token_updated_by: Optional[int] = None


# ── Products ──────────────────────────────────────────────────────────────────

class FakturowniaProductOut(BaseModel):
    """Single product from Fakturownia /products.json API."""
    model_config = {"extra": "forbid"}

    id: int
    name: str
    code: Optional[str] = None
    price_net: Optional[Decimal] = None
    currency: Optional[str] = None
    # RAO-P2-058: dodatkowe metadane dla snapshot na artykule
    tax: Optional[str] = None
    gtu_code: Optional[str] = None
    pkwiu: Optional[str] = None


# ── Invoices (raw from Fakturownia API) ───────────────────────────────────────

class InvoiceLine(BaseModel):
    """Single line item on a Fakturownia invoice."""
    model_config = {"extra": "forbid"}

    fakturownia_product_id: int
    fakturownia_product_name: str
    quantity: Decimal
    price_net: Decimal
    total_net: Decimal
    invoice_number: Optional[str] = None


class InvoiceOut(BaseModel):
    """Single invoice from Fakturownia (raw, before RAO article mapping)."""
    model_config = {"extra": "forbid"}

    invoice_number: str
    lines: List[InvoiceLine]
    total_net: Decimal


# ── Resolved invoices (1:N article mapping) ────────────────────────────────────

class RaoArticleRef(BaseModel):
    """Lightweight reference to a RAO article matched via fakturownia_product_id (1:N)."""
    model_config = {"extra": "forbid"}

    id: int
    name: str


class ResolvedInvoiceLine(BaseModel):
    """Invoice line enriched with 1:N RAO article mapping.

    Semantics (1:N):
    - rao_articles may contain 0 (unmapped) or N (mapped) RAO article refs.
    - If N > 1, the same Fakturownia product maps to multiple RAO articles.
      Each article gets the full line total_net (multiplication per spec).
    """
    model_config = {"extra": "forbid"}

    fakturownia_product_id: int
    fakturownia_product_name: str
    quantity: Decimal
    price_net: Decimal
    total_net: Decimal
    invoice_number: str
    rao_articles: List[RaoArticleRef] = []


class ResolvedInvoiceOut(BaseModel):
    """Invoice with 1:N article mappings resolved.

    mapped_total_net:
        Sum of (line.total_net × len(line.rao_articles)) for all lines with mappings.
        Example: line.total_net=1000, 3 RAO articles → contributes 3000 to mapped_total_net.

    unmapped_count:
        Number of lines with zero RAO article matches.
    """
    model_config = {"extra": "forbid"}

    invoice_number: str
    lines: List[ResolvedInvoiceLine]
    total_net: Decimal
    mapped_total_net: Decimal
    unmapped_count: int


# ── RAO-P2-058: Product cache (sync + search) ─────────────────────────────────

class SyncProductsResultOut(BaseModel):
    """Wynik synchronizacji katalogu produktów FA → lokalny cache."""
    model_config = {"extra": "forbid"}

    fetched: int
    upserted: int
    pages: int
    synced_at: datetime


class FakturowniaProductCacheOut(BaseModel):
    """Pojedynczy produkt z lokalnego cache (zapisany po sync-products)."""
    model_config = {"from_attributes": True, "extra": "forbid"}

    id: int
    product_id: int
    code: Optional[str] = None
    name: str
    price_net: Optional[Decimal] = None
    currency: Optional[str] = None
    tax_rate: Optional[str] = None
    gtu_code: Optional[str] = None
    pkwiu: Optional[str] = None
    synced_at: datetime
