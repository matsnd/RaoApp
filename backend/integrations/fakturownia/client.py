import httpx
import os
from typing import List, Optional
from decimal import Decimal

from .schemas import InvoiceLine, InvoiceOut


class FakturowniaClient:
    """Client Fakturownia API (read-only, MVP dla spike)."""
    
    def __init__(self):
        # MVP: hardcoded token z .env dla spike
        self.api_token = os.getenv("FAKTUROWNIA_API_TOKEN")
        self.domain_url = os.getenv("FAKTUROWNIA_DOMAIN_URL", "toolsmart")
        self.base_url = f"https://{self.domain_url}.fakturownia.pl"
        
    async def get_invoices_by_oid(self, oid: str) -> List[InvoiceOut]:
        """
        Pobierz faktury po numerze zamówienia (OID).
        
        MVP: mock implementation dla spike (zwraca dane testowe).
        W produkcji: prawdziwe zapytanie do Fakturownia API.
        """
        # TODO: W produkcji: prawdziwe zapytanie do Fakturownia API
        # MVP: mock data dla spike
        
        mock_invoices = [
            InvoiceOut(
                invoice_number=f"FV/2026/{oid}",
                lines=[
                    InvoiceLine(
                        fakturownia_product_id=12345,
                        fakturownia_product_name="Koparka CAT 320",
                        quantity=Decimal("1"),
                        price_net=Decimal("12000.00"),
                        total_net=Decimal("12000.00"),
                        invoice_number=f"FV/2026/{oid}"
                    ),
                    InvoiceLine(
                        fakturownia_product_id=12346,
                        fakturownia_product_name="Transport",
                        quantity=Decimal("1"),
                        price_net=Decimal("400.00"),
                        total_net=Decimal("400.00"),
                        invoice_number=f"FV/2026/{oid}"
                    )
                ],
                total_net=Decimal("12400.00")
            )
        ]
        
        return mock_invoices