"""
RAO-P2-012: Fakturownia REST API client.

Security:
- SSRF guard: domain_subdomain validated against ^[a-z0-9-]+$ (Pydantic + runtime).
  Domain suffix '.fakturownia.pl' is hardcoded — never user-supplied.
- httpx: verify=True (TLS), follow_redirects=False, timeout=10s.
- api_token passed as query param per Fakturownia API spec — never logged.
- 401 from Fakturownia → 502 upstream (bad token, not 401 to client — T1 fix).
"""
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import List

import httpx
from fastapi import HTTPException

from .schemas import FakturowniaProductOut, InvoiceLine, InvoiceOut

logger = logging.getLogger(__name__)

# SSRF guard — must match exactly before building URL
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9-]+$")
# Hardcoded suffix — never from user input
_DOMAIN_SUFFIX = ".fakturownia.pl"
_TIMEOUT = 10.0


class FakturowniaClient:
    """
    Read-only Fakturownia REST API client.

    Instantiate per-request with decrypted credentials from DB.
    Do NOT store or log api_token.
    """

    def __init__(self, domain_subdomain: str, api_token: str) -> None:
        # SSRF guard: validate subdomain at construction time
        if not domain_subdomain or not _SUBDOMAIN_RE.match(domain_subdomain):
            raise ValueError(
                f"Invalid domain_subdomain {domain_subdomain!r}. "
                "Must match ^[a-z0-9-]+$ (SSRF protection)"
            )
        # Suffix is hardcoded — attacker cannot escape to arbitrary hosts
        self._base_url = f"https://{domain_subdomain}{_DOMAIN_SUFFIX}"
        self._api_token = api_token  # ← NEVER log this field

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_invoices_by_oid(self, oid: str) -> List[InvoiceOut]:
        """Fetch invoices from Fakturownia by Order ID (OID = contract number in RAO).

        Fakturownia endpoint: GET /invoices.json?api_token=...&oid=...
        """
        raw = await self._get(
            "/invoices.json",
            params={"api_token": self._api_token, "oid": oid},
        )
        if not isinstance(raw, list):
            logger.warning(
                "Fakturownia /invoices.json returned non-list type: %s", type(raw).__name__
            )
            return []
        return self._parse_invoices(raw)

    async def get_products(self) -> List[FakturowniaProductOut]:
        """Fetch product catalogue from Fakturownia.

        Fakturownia endpoint: GET /products.json?api_token=...
        """
        raw = await self._get(
            "/products.json",
            params={"api_token": self._api_token},
        )
        if not isinstance(raw, list):
            logger.warning(
                "Fakturownia /products.json returned non-list type: %s", type(raw).__name__
            )
            return []
        return self._parse_products(raw)

    async def get_all_products(self, per_page: int = 100) -> tuple[List[FakturowniaProductOut], int]:
        """Fetch ALL products with pagination (RAO-P2-058).

        Returns (products, pages_fetched).
        Fakturownia API: GET /products.json?page=N&per_page=100&api_token=...
        """
        all_products: List[FakturowniaProductOut] = []
        page = 1
        pages = 0
        while True:
            raw = await self._get(
                "/products.json",
                params={
                    "api_token": self._api_token,
                    "page": page,
                    "per_page": per_page,
                },
            )
            if not isinstance(raw, list) or len(raw) == 0:
                break
            all_products.extend(self._parse_products(raw))
            pages += 1
            if len(raw) < per_page:
                break  # last page
            page += 1
            if page > 50:  # safety guard — 50 × 100 = 5000 products max
                logger.warning("Fakturownia get_all_products: hit safety guard at page 50")
                break
        return all_products, pages

    # ── HTTP layer ────────────────────────────────────────────────────────────

    async def _get(self, path: str, params: dict) -> object:
        url = f"{self._base_url}{path}"
        # NOTE: params dict contains api_token — do NOT log params
        try:
            async with httpx.AsyncClient(
                verify=True,
                follow_redirects=False,
                timeout=_TIMEOUT,
            ) as client:
                resp = await client.get(url, params=params)
        except httpx.TimeoutException:
            logger.warning("Fakturownia API timeout on %s", path)
            raise HTTPException(
                status_code=504,
                detail="Fakturownia API: przekroczono czas odpowiedzi (timeout 10s)",
            )
        except httpx.RequestError as exc:
            logger.error(
                "Fakturownia API connection error on %s: %s", path, type(exc).__name__
            )
            raise HTTPException(
                status_code=502,
                detail="Fakturownia API: błąd połączenia — sprawdź sieć/konfigurację",
            )

        self._check_status(resp, path)
        try:
            return resp.json()
        except ValueError as exc:
            logger.error("Fakturownia API returned non-JSON on %s: %s", path, type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail="Fakturownia API: nieprawidłowy format odpowiedzi (nie-JSON)",
            )

    def _check_status(self, resp: httpx.Response, path: str) -> None:
        if resp.status_code == 200:
            return
        # 401: bad token — surface as 502 (not 401 to avoid confusion with RAO auth)
        if resp.status_code == 401:
            raise HTTPException(
                status_code=502,
                detail="Fakturownia API: nieprawidłowy token API (HTTP 401) — zaktualizuj token w ustawieniach",
            )
        # 429: rate limit upstream
        if resp.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Fakturownia API: przekroczono limit zapytań (HTTP 429) — poczekaj chwilę",
            )
        # 302: redirect likely means bad subdomain (follow_redirects=False)
        if resp.status_code in (301, 302, 303, 307, 308):
            raise HTTPException(
                status_code=502,
                detail=(
                    "Fakturownia API: nieoczekiwane przekierowanie "
                    "(sprawdź domain_subdomain w ustawieniach)"
                ),
            )
        logger.error(
            "Fakturownia API HTTP %d on %s (URL: %s)", resp.status_code, path, resp.url
        )
        raise HTTPException(
            status_code=502,
            detail=f"Fakturownia API: błąd HTTP {resp.status_code}",
        )

    # ── Parsers ───────────────────────────────────────────────────────────────

    def _parse_invoices(self, data: list) -> List[InvoiceOut]:
        result: List[InvoiceOut] = []
        for inv in data:
            inv_number = str(inv.get("number") or inv.get("id") or "")
            positions = inv.get("positions") or []
            lines: List[InvoiceLine] = []
            for pos in positions:
                pid = pos.get("product_id")
                try:
                    lines.append(
                        InvoiceLine(
                            fakturownia_product_id=int(pid) if pid is not None else 0,
                            fakturownia_product_name=str(pos.get("name") or ""),
                            quantity=Decimal(str(pos.get("quantity") or 1)),
                            price_net=Decimal(str(pos.get("price_net") or 0)),
                            total_net=Decimal(str(pos.get("total_price_net") or 0)),
                            invoice_number=inv_number,
                        )
                    )
                except (TypeError, ValueError, InvalidOperation) as exc:
                    logger.warning("Fakturownia invoice line parse error: %s", exc)
                    continue
            try:
                total_net = Decimal(str(inv.get("price_net") or 0))
            except (TypeError, ValueError, InvalidOperation):
                total_net = Decimal("0")
            result.append(
                InvoiceOut(
                    invoice_number=inv_number,
                    lines=lines,
                    total_net=total_net,
                )
            )
        return result

    def _parse_products(self, data: list) -> List[FakturowniaProductOut]:
        result: List[FakturowniaProductOut] = []
        for p in data:
            try:
                price_net: Decimal | None = None
                if p.get("price_net") is not None:
                    price_net = Decimal(str(p["price_net"]))
                # RAO-P2-058: parse FA metadata for article snapshot
                gtu_raw = p.get("gtu_code")
                if not gtu_raw:
                    gtu_list = p.get("gtu_codes") or []
                    gtu_raw = gtu_list[0] if isinstance(gtu_list, list) and gtu_list else None
                result.append(
                    FakturowniaProductOut(
                        id=int(p.get("id") or 0),
                        name=str(p.get("name") or ""),
                        code=p.get("code") or None,
                        price_net=price_net,
                        currency=p.get("currency") or None,
                        tax=str(p.get("tax")) if p.get("tax") is not None else None,
                        gtu_code=str(gtu_raw) if gtu_raw else None,
                        pkwiu=p.get("additional_info") or None,
                    )
                )
            except (TypeError, ValueError, InvalidOperation) as exc:
                logger.warning("Fakturownia product parse error: %s", exc)
                continue
        return result
