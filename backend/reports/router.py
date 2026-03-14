from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from reports.service import generate_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/contract/{contract_id}")
async def generate_contract_report(
    contract_id: int,
    type: str = Query("contract"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pdf_bytes = await generate_pdf(db, contract_id, type)
    filename = f"umowa_{contract_id}_{type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
