from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from contracts.models import Contract
from reports.service import generate_pdf, generate_summary_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/contract/{contract_id}")
async def generate_contract_report(
    contract_id: int,
    type: str = Query("contract"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        pdf_bytes = await generate_pdf(db, contract_id, type)
    except Exception as exc:
        import traceback
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    contract = await db.get(Contract, contract_id)
    if contract:
        contract.print_date = datetime.utcnow()
        await db.commit()
    contract_num_clean = contract.number.replace('/', '_') if contract and contract.number else str(contract_id)
    filename = f"umowa_{contract_num_clean}_{type}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary/contractors")
async def summary_contractors(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pdf_bytes = await generate_summary_pdf(db, "contractors")
    filename = f"kontrahenci_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary/machines")
async def summary_machines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pdf_bytes = await generate_summary_pdf(db, "machines")
    filename = f"maszyny_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
