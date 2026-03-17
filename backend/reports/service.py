from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contractors.models import Contractor
from settings.models import Company, Salesperson, RateType
from articles.models import Article as ArticleModel


def generate_fees_text(fees: list) -> str:
    lines = []
    for f in sorted(fees, key=lambda x: x.sort_order):
        if not f.is_active:
            continue
        if f.amount_from and f.amount_to:
            kwota = f"{f.amount_from:.2f} zł - {f.amount_to:.2f} zł"
        elif f.amount_from:
            kwota = f"{f.amount_from:.2f} zł"
        else:
            kwota = ""
        unit = f" / {f.unit}" if f.unit else ""
        desc = f" ({f.description})" if f.description else ""
        lines.append(f"- {f.name}: {kwota}{unit}{desc}".strip())
    return "\n".join(lines)


def _build_conditions_text(conditions, default_unit: str = "doba") -> str:
    if not conditions:
        return ""
    sorted_conds = sorted(conditions, key=lambda c: (c.period_count or 0))
    lines = []
    prev_count = 0
    for i, c in enumerate(sorted_conds):
        unit = c.billing_label or default_unit
        rate = f"{float(c.rate1):.2f}" if c.rate1 else "0.00"
        rate2_str = f" - {float(c.rate2):.2f}" if c.rate2 else ""
        count = c.period_count or 0
        if i == 0:
            if count:
                lines.append(f"1 - {count} {unit} - {rate}{rate2_str} / {unit}")
            else:
                lines.append(c.description or f"{rate} / {unit}")
        else:
            lines.append(f"powyżej {prev_count} {unit} - {rate}{rate2_str} / {unit}")
        prev_count = count
    return "\n".join(lines)


async def build_contract_data(db: AsyncSession, contract_id: int) -> dict:
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        return {}

    contractor = await db.get(Contractor, contract.contractor_id)
    company = await db.get(Company, 1)
    salesperson = None
    if contract.salesperson_id:
        salesperson = await db.get(Salesperson, contract.salesperson_id)

    positions_result = await db.execute(
        select(ContractPosition).where(ContractPosition.contract_id == contract_id)
    )
    positions = positions_result.scalars().all()

    positions_data = []
    for pos in positions:
        conds_result = await db.execute(
            select(PositionCondition).where(PositionCondition.position_id == pos.id)
        )
        conditions = conds_result.scalars().all()
        rate_type = None
        if pos.rate_type_id:
            rate_type = await db.get(RateType, pos.rate_type_id)

        article = await db.get(ArticleModel, pos.article_id) if pos.article_id else None

        conditions_text = _build_conditions_text(conditions, pos.billing_unit or "doba")

        positions_data.append({
            "pos": pos,
            "conditions": conditions,
            "conditions_text": conditions_text,
            "rate_type_name": rate_type.name if rate_type else None,
            "replacement_value": article.replacement_value if article else None,
            "serial_no": article.serial_no if article else None,
            "registration_no": article.registration_no if article else None,
        })

    fees_result = await db.execute(
        select(ContractServiceFee)
        .where(ContractServiceFee.contract_id == contract_id)
        .order_by(ContractServiceFee.sort_order)
    )
    fees = fees_result.scalars().all()

    return {
        "contract": contract,
        "contractor": contractor,
        "company": company,
        "salesperson": salesperson,
        "positions": positions_data,
        "fees": fees,
        "fees_text": generate_fees_text(fees),
    }


async def generate_summary_pdf(db: AsyncSession, summary_type: str) -> bytes:
    import asyncio
    from sqlalchemy import select
    from contractors.models import Contractor
    from articles.models import Article

    if summary_type == "contractors":
        result = await db.execute(select(Contractor).order_by(Contractor.name))
        items = result.scalars().all()
        html = """<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:sans-serif;font-size:11px;color:#222;padding:20px;}
        h1{font-size:15px;color:#1D2B53;margin-bottom:12px;}
        table{width:100%;border-collapse:collapse;}
        th{background:#1D2B53;color:#fff;padding:5px 8px;text-align:left;font-size:10px;}
        td{padding:4px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}
        tr:nth-child(even) td{background:#f7f8ff;}</style></head><body>
        <h1>Zestawienie Kontrahentów</h1>
        <table><thead><tr><th>#</th><th>Nazwa</th><th>NIP</th><th>Miasto</th><th>Telefon</th><th>Email</th></tr></thead><tbody>"""
        for i, c in enumerate(items, 1):
            html += f"<tr><td>{i}</td><td>{c.name or ''}</td><td>{c.nip or '—'}</td><td>{c.city or '—'}</td><td>{c.phone1 or '—'}</td><td>{c.email or '—'}</td></tr>"
        html += "</tbody></table></body></html>"
    else:
        result = await db.execute(select(Article).order_by(Article.name))
        items = result.scalars().all()
        html = """<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:sans-serif;font-size:11px;color:#222;padding:20px;}
        h1{font-size:15px;color:#1D2B53;margin-bottom:12px;}
        table{width:100%;border-collapse:collapse;}
        th{background:#1D2B53;color:#fff;padding:5px 8px;text-align:left;font-size:10px;}
        td{padding:4px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}
        tr:nth-child(even) td{background:#f7f8ff;}</style></head><body>
        <h1>Zestawienie Maszyn / Artykułów</h1>
        <table><thead><tr><th>#</th><th>Nazwa</th><th>Typ</th><th>Nr wew.</th><th>Nr rej.</th><th>Marka/Model</th></tr></thead><tbody>"""
        for i, a in enumerate(items, 1):
            typ = "Usługa" if a.is_service else "Sprzęt"
            marka = f"{a.brand or ''} {a.model or ''}".strip() or "—"
            html += f"<tr><td>{i}</td><td>{a.name}</td><td>{typ}</td><td>{a.internal_number or '—'}</td><td>{a.registration_no or '—'}</td><td>{marka}</td></tr>"
        html += "</tbody></table></body></html>"

    return await asyncio.get_event_loop().run_in_executor(None, _html_to_pdf_sync, html)


def _html_to_pdf_sync(html: str) -> bytes:
    """Render HTML to PDF using Playwright (Chromium). Handles Polish characters correctly."""
    from playwright.sync_api import sync_playwright
    import datetime
    
    now = datetime.datetime.now().strftime("%d.%m.%Y")
    
    footer_template = f"""<div style="font-size: 8px; color: #444; width: 100%; padding: 0 14mm; display: flex; justify-content: space-between; font-family: Arial;">
      <span>Wydrukowano {now}</span>
      <span>Strona <span class="pageNumber"></span> z <span class="totalPages"></span></span>
    </div>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=footer_template,
            margin={"top": "0", "bottom": "15mm", "left": "0", "right": "0"}
        )
        browser.close()
    return pdf_bytes


def _fmt_date_pl(d) -> str:
    """Format date as dd.mm.yyyy"""
    if d is None:
        return ''
    if hasattr(d, 'strftime'):
        return d.strftime('%d.%m.%Y')
    return str(d)


def _fmt_money(v) -> str:
    """Format number as Polish currency string with zł suffix: 3 198,00 zł"""
    if v is None:
        return ''
    try:
        f = float(v)
        formatted = f"{f:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '\u00a0')
        return formatted + '\u00a0z\u0142'
    except (TypeError, ValueError):
        return str(v)


def _fmt_money_plain(v) -> str:
    """Format number as Polish number without zł: 3 198,00"""
    if v is None:
        return ''
    try:
        f = float(v)
        return f"{f:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '\u00a0')
    except (TypeError, ValueError):
        return str(v)


async def generate_pdf(db: AsyncSession, contract_id: int, report_type: str = "contract") -> bytes:
    from jinja2 import Environment, FileSystemLoader
    import asyncio
    import os

    data = await build_contract_data(db, contract_id)
    if not data:
        raise ValueError(f"Contract {contract_id} not found")

    contract = data.get("contract")
    contract_type = getattr(contract, 'contract_type', 'S') if contract else 'S'
    is_service = (contract_type == 'U')

    template_map = {
        "contract":            "contract_u.html" if is_service else "contract.html",
        "contract_s":          "contract.html",
        "contract_u":          "contract_u.html",
        "protocol_zo":         "protocol_zo_u.html" if is_service else "protocol_zo.html",
        "protocol_zo_s":       "protocol_zo.html",
        "protocol_zo_u":       "protocol_zo_u.html",
        "protocol_zo_nodata":  "protocol_zo_nodata_u.html" if is_service else "protocol_zo_nodata.html",
        "protocol_zo_nodata_s": "protocol_zo_nodata.html",
        "protocol_zo_nodata_u": "protocol_zo_nodata_u.html",
    }
    template_name = template_map.get(report_type, "contract.html")

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['datepl'] = _fmt_date_pl
    env.filters['money'] = _fmt_money
    env.filters['money_plain'] = _fmt_money_plain

    try:
        template = env.get_template(template_name)
    except Exception:
        template = env.get_template("contract.html")

    from datetime import datetime
    data["now"] = datetime.now().strftime("%d.%m.%Y")
    html = template.render(**data)

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, _html_to_pdf_sync, html)
    return pdf_bytes
