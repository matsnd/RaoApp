from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class InvoiceLine(BaseModel):
    fakturownia_product_id: int
    fakturownia_product_name: str
    quantity: Decimal
    price_net: Decimal
    total_net: Decimal
    invoice_number: Optional[str] = None


class InvoiceOut(BaseModel):
    invoice_number: str
    lines: List[InvoiceLine]
    total_net: Decimal