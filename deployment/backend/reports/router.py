from datetime import datetime, date
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from contracts.models import Contract
from contractors.models import Contractor
from settings.models import Company, Salesperson
from contracts.service import compute_print_hash
from reports.service import generate_pdf, generate_summary_pdf, generate_commissions_pdf, generate_stats_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _content_disposition(filename: str) -> str:
    """RFC 5987 — bezpieczna obsługa polskich znaków w nazwie pliku."""
    ascii_name = filename.encode('ascii', errors='replace').decode('ascii')
    utf8_name = quote(filename, safe='')
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"


def _check_contract_access(contract: Contract, current_user: User) -> None:
    """RAO-SEC-001: IDOR fix — ownership check na poziomie branch.

    Admin: pełny dostęp do wszystkich umów.
    Non-admin: tylko umowy z własnego branch (branch_id match).
    Umowy bez branch (NULL) = legacy, dostępne dla wszystkich zalogowanych.

    NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. No-op.
    Pełny RBAC wdrożony gdy pojawią się wymagania wieloużytkownikowe.
    """
    return  # no-op — single-user mode


@router.post("/contract/{contract_id}")
async def generate_contract_report(
    contract_id: int,
    type: str = Query("contract", pattern="^(contract|protocol_zo|protocol_zo_s|protocol_zo_u|protocol_zo_nodata|protocol_zo_nodata_s|protocol_zo_nodata_u)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # RAO-SEC-001: IDOR fix — fetch contract first, check ownership before PDF generation
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Umowa nie znaleziona")
    _check_contract_access(contract, current_user)

    try:
        pdf_bytes = await generate_pdf(db, contract_id, type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Umowa nie znaleziona")
    except Exception as exc:
        import logging
        logging.exception("PDF generation failed for contract_id=%s type=%s", contract_id, type)
        raise HTTPException(status_code=500, detail="Błąd generowania raportu")
    if contract:
        # RAO: compute + store print_hash for staleness detection
        contractor = await db.get(Contractor, contract.contractor_id)
        company = await db.get(Company, 1)
        salesperson = await db.get(Salesperson, contract.salesperson_id) if contract.salesperson_id else None
        p_hash = await compute_print_hash(db, contract, contractor, company, salesperson)
        contract.print_date = datetime.utcnow()
        contract.print_hash = p_hash
        await db.commit()
    contract_num_clean = contract.number.replace('/', '_') if contract and contract.number else str(contract_id)

    # Determine filename (folder auto-save is handled by frontend usePdfFolders — IndexedDB)
    if type == 'contract':
        filename = f"{contract_num_clean}.pdf"
    else:
        filename = f"PZO_{contract_num_clean}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


def _require_admin(user: User):
    """RAO-SEC-009: Summary reports contain cross-branch data — admin only.

    NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. No-op.
    Pełny RBAC wdrożony gdy pojawią się wymagania wieloużytkownikowe.
    """
    return  # no-op — single-user mode


@router.get("/summary/contractors")
async def summary_contractors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    pdf_bytes = await generate_summary_pdf(db, "contractors")
    filename = f"Kontrahenci_{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/summary/machines")
async def summary_machines(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    pdf_bytes = await generate_summary_pdf(db, "machines")
    filename = f"Maszyny_{datetime.utcnow().strftime('%Y-%m-%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/summary/commissions")
async def summary_commissions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    today = datetime.utcnow().date()
    df = date_from or today.replace(day=1)
    dt = date_to or today
    pdf_bytes = await generate_commissions_pdf(db, df, dt)
    filename = f"Prowizje_{df.strftime('%Y-%m-%d')}_{dt.strftime('%Y-%m-%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/summary/stats")
async def summary_stats(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    today = datetime.utcnow().date()
    df = date_from or today.replace(day=1)
    dt = date_to or today
    pdf_bytes = await generate_stats_pdf(db, df, dt)
    filename = f"Statystyki_{df.strftime('%Y-%m-%d')}_{dt.strftime('%Y-%m-%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )
