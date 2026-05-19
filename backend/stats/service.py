"""
RAO-P3-004: Serwis eksportu CSV dla statystyk.

Logika biznesowa oddzielona od routera zgodnie z architekturą modułową RAO.
Używa wyłącznie standardowej biblioteki Python (csv + io) — bez zewnętrznych zależności.
"""
import csv
import io
from datetime import date
from typing import Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from articles.models import Article
from contracts.models import Contract, ContractPosition
from contractors.models import Contractor

# Delimiter dla polskiego Excela (średnik zamiast przecinka — PL locale)
_CSV_DELIMITER = ";"

# Nagłówki kolumn per typ eksportu
_HEADERS: dict[str, list[str]] = {
    "contracts": [
        "nr_umowy", "kontrahent", "data_od", "data_do",
        "status", "handlowiec", "wartosc_netto",
    ],
    "articles": ["nazwa", "kategoria", "nr_wewn", "aktywna_umowa"],
    "contractors": ["nazwa", "nip", "miasto", "email", "telefon", "aktywna_umowa"],
}


def build_csv_string(
    export_type: Literal["contracts", "articles", "contractors"],
    rows: list[dict],
) -> str:
    """
    Pure function: buduje string CSV z listy słowników.
    Testowalna bez DB.

    Każdy dict powinien mieć klucze odpowiadające nagłówkom dla danego export_type.
    Brakujące klucze -> pusty string.

    Returns:
        UTF-8 BOM string (\\ufeff + nagłówek + wiersze danych).
        Delimiter: średnik (PL Excel).
    """
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM — Excel poprawnie otwiera polskie znaki
    writer = csv.writer(output, delimiter=_CSV_DELIMITER)
    headers = _HEADERS[export_type]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return output.getvalue()


async def export_csv_data(
    db: AsyncSession,
    export_type: Literal["contracts", "articles", "contractors"],
    from_date: date | None,
    to_date: date | None,
) -> str:
    """
    Pobiera dane z DB i zwraca string CSV (UTF-8 BOM).

    Args:
        db: sesja async SQLAlchemy
        export_type: typ eksportu (contracts | articles | contractors)
        from_date: opcjonalny filtr od daty (Contract.date_from dla type=contracts)
        to_date: opcjonalny filtr do daty (Contract.date_from dla type=contracts)

    Returns:
        UTF-8 BOM CSV string gotowy do StreamingResponse.
    """
    if export_type == "contracts":
        rows = await _query_contracts(db, from_date, to_date)
    elif export_type == "articles":
        rows = await _query_articles(db)
    else:  # contractors
        rows = await _query_contractors(db)
    return build_csv_string(export_type, rows)


# ---------------------------------------------------------------------------
# Prywatne funkcje pomocnicze — zapytania DB
# ---------------------------------------------------------------------------

async def _query_contracts(
    db: AsyncSession,
    from_date: date | None,
    to_date: date | None,
) -> list[dict]:
    """Pobiera listę umów z opcjonalnym filtrem dat."""
    from settings.models import Salesperson

    today = date.today()

    stmt = (
        select(
            Contract.number,
            Contract.contractor_name,
            Contract.date_from,
            Contract.date_to,
            Contract.salesperson_id,
            Contract.total_value,
        )
        .order_by(Contract.date_from.desc())
    )
    if from_date:
        stmt = stmt.where(Contract.date_from >= from_date)
    if to_date:
        stmt = stmt.where(Contract.date_from <= to_date)

    result = await db.execute(stmt)
    raw = result.all()

    # Batch-fetch nazw handlowcow (unikamy N+1)
    sp_ids = {r[4] for r in raw if r[4]}
    sp_map: dict[int, str] = {}
    if sp_ids:
        sp_q = await db.execute(
            select(Salesperson.id, Salesperson.name)
            .where(Salesperson.id.in_(sp_ids))
        )
        sp_map = {r[0]: r[1] for r in sp_q.all()}

    rows: list[dict] = []
    for r in raw:
        # Status umowy na podstawie dat
        if r[3] and r[3] < today:
            status = "zakonczona"
        elif r[2] and r[2] <= today:
            status = "aktywna"
        else:
            status = "przyszla"

        # Wartosc netto: decimal -> string z przecinkiem (PL format)
        wartosc = str(r[5]).replace(".", ",") if r[5] is not None else "0"

        rows.append({
            "nr_umowy": r[0] or "",
            "kontrahent": r[1] or "",
            "data_od": r[2].strftime("%d.%m.%Y") if r[2] else "",
            "data_do": r[3].strftime("%d.%m.%Y") if r[3] else "",
            "status": status,
            "handlowiec": sp_map.get(r[4], "") if r[4] else "",
            "wartosc_netto": wartosc,
        })
    return rows


async def _query_articles(db: AsyncSession) -> list[dict]:
    """Pobiera listę artykułów (niearchiwalnych) z flagą aktywnej umowy."""
    today = date.today()

    stmt = (
        select(
            Article.id,
            Article.name,
            Article.category_main,
            Article.internal_number,
        )
        .where(Article.is_archival == False)  # noqa: E712
        .order_by(Article.name)
    )
    result = await db.execute(stmt)
    arts = result.all()

    # Sprawdz które artykuly maja aktywne umowy (batch query — bez N+1)
    active_ids: set[int] = set()
    if arts:
        art_ids = [a[0] for a in arts]
        active_q = await db.execute(
            select(ContractPosition.article_id)
            .join(Contract, Contract.id == ContractPosition.contract_id)
            .where(
                and_(
                    ContractPosition.article_id.in_(art_ids),
                    Contract.date_from <= today,
                    Contract.date_to >= today,
                )
            )
            .distinct()
        )
        active_ids = {r[0] for r in active_q.all()}

    return [
        {
            "nazwa": a[1] or "",
            "kategoria": a[2] or "",
            "nr_wewn": a[3] or "",
            "aktywna_umowa": "tak" if a[0] in active_ids else "nie",
        }
        for a in arts
    ]


async def _query_contractors(db: AsyncSession) -> list[dict]:
    """Pobiera listę kontrahentów z flagą aktywnej umowy."""
    today = date.today()

    stmt = (
        select(
            Contractor.id,
            Contractor.name,
            Contractor.nip,
            Contractor.city,
            Contractor.email,
            Contractor.phone1,
        )
        .order_by(Contractor.name)
    )
    result = await db.execute(stmt)
    ctrs = result.all()

    # Sprawdz które kontrahenty maja aktywne umowy (batch query — bez N+1)
    active_ids = set()
    if ctrs:
        c_ids = [c[0] for c in ctrs]
        active_q = await db.execute(
            select(Contract.contractor_id)
            .where(
                and_(
                    Contract.contractor_id.in_(c_ids),
                    Contract.date_from <= today,
                    Contract.date_to >= today,
                )
            )
            .distinct()
        )
        active_ids = {r[0] for r in active_q.all()}

    return [
        {
            "nazwa": c[1] or "",
            "nip": c[2] or "",
            "miasto": c[3] or "",
            "email": c[4] or "",
            "telefon": c[5] or "",
            "aktywna_umowa": "tak" if c[0] in active_ids else "nie",
        }
        for c in ctrs
    ]
