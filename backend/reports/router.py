from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from contracts.models import Contract
from reports.service import generate_pdf, generate_summary_pdf, generate_commissions_pdf, generate_stats_pdf

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


@router.get("/summary/commissions")
async def summary_commissions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.utcnow().date()
    df = date_from or today.replace(day=1)
    dt = date_to or today
    pdf_bytes = await generate_commissions_pdf(db, df, dt)
    filename = f"prowizje_{df.strftime('%Y%m%d')}_{dt.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary/stats")
async def summary_stats(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.utcnow().date()
    df = date_from or today.replace(day=1)
    dt = date_to or today
    pdf_bytes = await generate_stats_pdf(db, df, dt)
    filename = f"statystyki_{df.strftime('%Y%m%d')}_{dt.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
