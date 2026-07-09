from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from database import get_db
from auth.dependencies import get_current_user
from auth.models import User
from .schemas import (
    ContractSettlementResponse,
    ContractSettlementCreate,
    ContractSettlementUpdate,
)
from .service import SettlementService
from .models import ContractSettlement
from contracts.models import ContractPosition

router = APIRouter(prefix="/settlements", tags=["settlements"])
service = SettlementService()


@router.get("/contract/{contract_id}", response_model=list[ContractSettlementResponse])
async def get_contract_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pobierz wszystkie rozliczenia dla umowy."""
    return await service.get_settlements_by_contract(db, contract_id)


@router.get("/{settlement_id}", response_model=ContractSettlementResponse)
async def get_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pobierz pojedyncze rozliczenie."""
    settlement = await service.get_settlement(db, settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return settlement


@router.post("", response_model=ContractSettlementResponse)
async def create_settlement(
    data: ContractSettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Utwórz nowe rozliczenie."""
    return await service.create_settlement(db, data)


@router.put("/{settlement_id}", response_model=ContractSettlementResponse)
async def update_settlement(
    settlement_id: int,
    data: ContractSettlementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Zaktualizuj rozliczenie."""
    settlement = await service.update_settlement(db, settlement_id, data)
    if not settlement:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return settlement


@router.post("/contract/{contract_id}/init")
async def init_contract_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """RAO-P1-012: Inicjuj rozliczenia dla umowy.

    Idempotentnie: najpierw usuwa poprzednie pozycje, potem buduje na nowo
    z aktualnych pozycji umowy oraz aktywnych usług dodatkowych.
    """
    await service.init_settlements_from_contract(db, contract_id)
    return await service.get_settlements_by_contract(db, contract_id)


@router.post("/contract/{contract_id}/init-from-fakturownia")
async def init_contract_settlements_from_fakturownia(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RAO-P2-012: Inicjuj rozliczenia dla umowy z Fakturownia.

    Pobiera faktury z Fakturownia dla umowy (przez OID) i mapuje pozycje faktury
    na pozycje umowy przez fakturownia_product_id (1:N mapping).

    RAO-P2-012: Również pobiera usługi dodatkowe (contract_service_fees) z Fakturownia.

    RAO-P2-032 security: Rate limit 30/min/user (spójne z /integrations/fakturownia/invoices).

    Logika mapowania:
    - Pobiera faktury z Fakturownia przez integrations/fakturownia/service
    - Dla pozycji umowy: sprawdza czy są artykuły RAO ze zmapowanym fakturownia_product_id
      Jeśli artykuł jest na umowie → tworzy/aktualizuje settlement z cost_client z faktury
    - Dla usług dodatkowych: sprawdza czy service_fee_templates mają article_id z fakturownia_product_id
      Jeśli artykuł jest zmapowany → tworzy/aktualizuje settlement z service_fee_id
    - Semantyka 1:N: jeśli produkt FA jest przypisany do wielu artykułów RAO,
      każdy artykuł na umowie dostaje pełną wartość z faktury (multiplikacja OK)
    """
    # RAO-P2-032 security: rate limit (zapobiega DDoS Fakturownia API)
    from integrations.fakturownia.router import _invoices_limiter
    rl_key = f"invoices:user:{current_user.id}"
    if not _invoices_limiter.is_allowed(rl_key):
        raise HTTPException(
            status_code=429,
            detail="Zbyt wiele zapytan o faktury — odczekaj chwile (limit: 30/min)",
        )

    from integrations.fakturownia.service import fetch_invoices_for_contract
    from articles.models import Article
    from contracts.models import ContractServiceFee
    from settings.models import ServiceFeeTemplate

    # Pobierz faktury z Fakturownia
    try:
        invoices = await fetch_invoices_for_contract(db, contract_id, current_user)
    except HTTPException as e:
        if e.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail="Umowa nie posiada numeru OID (zamówienie Fakturownia). Wpisz OID w polu 'OID (zamówienie Fakturownia)' przed pobraniem."
            )
        raise
    
    if not invoices:
        raise HTTPException(status_code=404, detail="Brak faktur w Fakturownia dla tej umowy")
    
    # Pobierz pozycje umowy z artykułami (dla mapowania)
    positions = await db.execute(
        select(ContractPosition, Article)
        .join(Article, ContractPosition.article_id == Article.id)
        .where(ContractPosition.contract_id == contract_id)
    )
    position_articles = positions.all()
    
    # Map: position_id -> (position, article)
    pos_to_article = {pa[0].id: (pa[0], pa[1]) for pa in position_articles}
    
    # Map: fakturownia_product_id -> list[position_id]
    pid_to_positions = {}
    for pos, art in pos_to_article.values():
        if art.fakturownia_product_id:
            pid_to_positions.setdefault(art.fakturownia_product_id, []).append(pos.id)
    
    # Pobierz usługi dodatkowe umowy z szablonami (dla mapowania)
    service_fees = await db.execute(
        select(ContractServiceFee, ServiceFeeTemplate)
        .join(ServiceFeeTemplate, ContractServiceFee.name == ServiceFeeTemplate.name)
        .where(ContractServiceFee.contract_id == contract_id)
    )
    fee_templates = service_fees.all()
    
    # Map: service_fee_id -> (fee, template)
    fee_to_template = {ft[0].id: (ft[0], ft[1]) for ft in fee_templates}
    
    # Map: fakturownia_product_id -> list[service_fee_id]
    pid_to_service_fees = {}
    for fee, template in fee_to_template.values():
        if template.article_id:
            article_result = await db.execute(select(Article).where(Article.id == template.article_id))
            article = article_result.scalar_one_or_none()
            if article and article.fakturownia_product_id:
                pid_to_service_fees.setdefault(article.fakturownia_product_id, []).append(fee.id)
    
    # RAO Faza 2a (opcja E): zbiór wszystkich zmapowanych product_id (positions + service_fees).
    # Blok unmapped w obu pętlach sprawdza pid not in mapped_pids — chroni przed
    # double-counting (pozycja FA zmapowana jako service_fee nie dostaje unmapped w pętli 1,
    # pozycja FA zmapowana jako position nie dostaje unmapped w pętli 2).
    mapped_pids = set(pid_to_positions.keys()) | set(pid_to_service_fees.keys())
    
    # Przetwórz faktury i utwórz/aktualizuj settlements dla pozycji
    for invoice in invoices:
        for line in invoice.lines:
            pid = line.fakturownia_product_id
            position_ids = pid_to_positions.get(pid, [])

            if not position_ids:
                # RAO Faza 2a (opcja E): unmapped pozycje FA — tworzenie settlement
                # bez position_id (snapshot nazwy w article_name_snapshot).
                # NIE tworzymy artykułu on-the-fly — tylko snapshot nazwy.
                # Idempotentność: UNIQUE(unmapped_key) chroni przed duplikatem.
                if pid is not None and pid != 0:
                    existing = await db.execute(
                        select(ContractSettlement).where(
                            ContractSettlement.contract_id == contract_id,
                            ContractSettlement.position_id.is_(None),
                            ContractSettlement.service_fee_id.is_(None),
                            ContractSettlement.fakturownia_product_id == pid,
                            ContractSettlement.fakturownia_invoice_number == line.invoice_number,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(ContractSettlement(
                            contract_id=contract_id,
                            position_id=None,
                            service_fee_id=None,
                            cost_client=float(line.total_net),
                            cost_company=None,
                            source="fa_unmapped",
                            article_name_snapshot=line.fakturownia_product_name,
                            fakturownia_product_id=pid,
                            fakturownia_invoice_number=line.invoice_number,
                            settled_at=invoice.issue_date,
                            notes=f"Pobrano z faktury {line.invoice_number} (pozycja niezmapowana)",
                        ))
                continue  # Brak pozycji umowy z tym produktem FA

            # Semantyka 1:N: każda pozycja umowy dostaje pełną wartość z faktury
            cost_client = float(line.total_net)

            for position_id in position_ids:
                existing = await db.execute(
                    select(ContractSettlement).where(
                        ContractSettlement.contract_id == contract_id,
                        ContractSettlement.position_id == position_id,
                    )
                )
                existing_settlement = existing.scalar_one_or_none()

                if existing_settlement:
                    # Zaktualizuj istniejące
                    # RAO Faza 2a (opcja E) bug fix bonus (QA bug 1.7):
                    # source='fakturownia' (nie domyślne 'manual') + settled_at z invoice
                    existing_settlement.cost_client = cost_client
                    existing_settlement.source = "fakturownia"
                    existing_settlement.settled_at = invoice.issue_date
                    existing_settlement.fakturownia_invoice_number = line.invoice_number
                    existing_settlement.updated_at = datetime.utcnow()
                else:
                    # Utwórz nowe
                    settlement = ContractSettlement(
                        contract_id=contract_id,
                        position_id=position_id,
                        service_fee_id=None,
                        cost_client=cost_client,
                        cost_company=None,
                        source="fakturownia",
                        settled_at=invoice.issue_date,
                        fakturownia_invoice_number=line.invoice_number,
                        notes=f"Pobrano z faktury {line.invoice_number}"
                    )
                    db.add(settlement)

    # Przetwórz faktury i utwórz/aktualizuj settlements dla usług dodatkowych
    for invoice in invoices:
        for line in invoice.lines:
            pid = line.fakturownia_product_id
            service_fee_ids = pid_to_service_fees.get(pid, [])

            if not service_fee_ids:
                # RAO Faza 2a (opcja E): unmapped — analogiczny blok co dla pozycji.
                # Nie rozróżniamy maszyna/usługa dla unmapped (nie mamy is_service).
                # UWAGA: ten sam produkt FA mógł być już dodany jako unmapped w pętli
                # pozycji powyżej — UNIQUE(unmapped_key) chroni przed duplikatem
                # (klucz = unmapped:pid:invoice_number, identyczny niezależnie od
                # tego, w której pętli próbujemy dodać).
                if pid is not None and pid != 0:
                    existing = await db.execute(
                        select(ContractSettlement).where(
                            ContractSettlement.contract_id == contract_id,
                            ContractSettlement.position_id.is_(None),
                            ContractSettlement.service_fee_id.is_(None),
                            ContractSettlement.fakturownia_product_id == pid,
                            ContractSettlement.fakturownia_invoice_number == line.invoice_number,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(ContractSettlement(
                            contract_id=contract_id,
                            position_id=None,
                            service_fee_id=None,
                            cost_client=float(line.total_net),
                            cost_company=None,
                            source="fa_unmapped",
                            article_name_snapshot=line.fakturownia_product_name,
                            fakturownia_product_id=pid,
                            fakturownia_invoice_number=line.invoice_number,
                            settled_at=invoice.issue_date,
                            notes=f"Pobrano z faktury {line.invoice_number} (pozycja niezmapowana)",
                        ))
                continue  # Brak usług dodatkowych z tym produktem FA

            # Semantyka 1:N: każda usługa dodatkowa dostaje pełną wartość z faktury
            cost_client = float(line.total_net)

            for service_fee_id in service_fee_ids:
                existing = await db.execute(
                    select(ContractSettlement).where(
                        ContractSettlement.contract_id == contract_id,
                        ContractSettlement.service_fee_id == service_fee_id,
                    )
                )
                existing_settlement = existing.scalar_one_or_none()

                if existing_settlement:
                    # Zaktualizuj istniejące
                    # RAO Faza 2a (opcja E) bug fix bonus (QA bug 1.7):
                    # source='fakturownia' (nie domyślne 'manual') + settled_at z invoice
                    existing_settlement.cost_client = cost_client
                    existing_settlement.source = "fakturownia"
                    existing_settlement.settled_at = invoice.issue_date
                    existing_settlement.fakturownia_invoice_number = line.invoice_number
                    existing_settlement.updated_at = datetime.utcnow()
                else:
                    # Utwórz nowe
                    settlement = ContractSettlement(
                        contract_id=contract_id,
                        position_id=None,
                        service_fee_id=service_fee_id,
                        cost_client=cost_client,
                        cost_company=None,
                        source="fakturownia",
                        settled_at=invoice.issue_date,
                        fakturownia_invoice_number=line.invoice_number,
                        notes=f"Pobrano z faktury {line.invoice_number}"
                    )
                    db.add(settlement)
    
    await db.commit()
    return await service.get_settlements_by_contract(db, contract_id)


@router.delete("/{settlement_id}")
async def delete_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Usuń rozliczenie."""
    deleted = await service.delete_settlement(db, settlement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return {"message": "Rozliczenie usunięte"}


@router.delete("/contract/{contract_id}/all")
async def clear_all_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """P0-013: Wyczyść wszystkie rozliczenia dla umowy (bulk DELETE).

    Operator potrzebuje korekt po pobraniu z Fakturownia (np. faktura zawiera
    pozycje niepasujące do umowy, błędne kwoty, duplikaty).
    """
    # Weryfikacja: umowa istnieje
    from contracts.models import Contract
    contract = await db.execute(select(Contract).where(Contract.id == contract_id))
    if not contract.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Umowa nie znaleziona")

    count = await service.clear_settlements_by_contract(db, contract_id)
    return {"message": f"Usunięto {count} rozliczeń", "deleted_count": count}