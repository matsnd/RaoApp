from fastapi import APIRouter, Depends, Query
from typing import List

from auth.dependencies import get_current_user
from .client import FakturowniaClient
from .schemas import InvoiceOut

router = APIRouter(prefix="/integrations/fakturownia", tags=["fakturownia"])

client = FakturowniaClient()


@router.get("/invoices", response_model=List[InvoiceOut])
async def get_invoices_by_oid(
    oid: str = Query(..., description="Numer zamówienia (OID)"),
    current_user = Depends(get_current_user)
):
    """
    Pobierz faktury z Fakturownia po numerze zamówienia (OID).

    MVP: read-only, bez DB, bez mapping.
    """
    invoices = await client.get_invoices_by_oid(oid)
    return invoices