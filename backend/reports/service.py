import pathlib
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contractors.models import Contractor
from settings.models import Company, Salesperson, RateType
from machines.models import Machine as MachineModel


_FEE_PLACEHOLDER_RE = re.compile(r"\$(1|2)")


def _resolve_fee_description(desc: str, amount_from, amount_to) -> str:
    """Replace $1/$2 placeholders with formatted amounts + zł.

    Missing amount -> '0,00 zł' so the printed line never contains a '$'.
    """
    if not desc:
        return desc

    def _amount_text(value):
        if value is None:
            return _fmt_money(0)
        return _fmt_money(value)

    def _repl(match: re.Match) -> str:
        return _amount_text(amount_from if match.group(1) == "1" else amount_to)

    return _FEE_PLACEHOLDER_RE.sub(_repl, desc)


def generate_fees_text(fees: list) -> str:
    """Build human-readable fees text.

    RAO-P0-032: Accepts either raw ContractServiceFee objects (legacy) or
    dicts with {"fee": ContractServiceFee, "description": str} (new format
    that avoids mutating attached session objects).

    RAO-P1-100: KISS redesign — "Tekst na umowie" (description) is used as-is
    when filled. Fallback to legacy amount/unit formatting only if description is empty.
    """
    lines = []
    # Normalize: extract (fee, description) pairs
    normalized = []
    for item in fees:
        if isinstance(item, dict) and "fee" in item:
            normalized.append((item["fee"], item.get("description") or item["fee"].description))
        else:
            normalized.append((item, item.description))
    for f, desc in sorted(normalized, key=lambda x: x[0].sort_order):
        if not f.is_active:
            continue
        desc = (desc or "").strip()
        if desc:
            desc = _resolve_fee_description(desc, f.amount_from, f.amount_to)
            lines.append(f"- {f.name}: {desc}")
        else:
            amount_line = _build_fee_amount_line(f)
            if amount_line:
                lines.append(f"- {f.name}: {amount_line}")
            else:
                lines.append(f"- {f.name}")
    return "\n".join(lines)


# RAO-P1-045: _build_conditions_text removed — dead code.
# build_contract_data already uses format_position_conditions_cascading (dedup + cascading).


def _build_fee_amount_line(fee: ContractServiceFee) -> str:
    """Format amount for PDF service-fee display (description is the single source of truth;
    this fallback only formats the raw amount when description is empty).

    RAO-P0-050: Decimal(0) is truthy-by-value but falsy in Python; use is not None.
    RAO-P1-102: KISS — unit (JM) removed; description carries the full printed text.
    """
    if fee.amount_from is None and fee.amount_to is None:
        return ""
    if fee.amount_from is not None and fee.amount_to is not None and fee.amount_to == fee.amount_from:
        return _fmt_money(fee.amount_from)
    if fee.amount_from is not None and fee.amount_to is not None:
        return f"{_fmt_money(fee.amount_from)} - {_fmt_money(fee.amount_to)}"
    if fee.amount_from is not None:
        return _fmt_money(fee.amount_from)
    return _fmt_money(fee.amount_to)


def _format_fee_display(fee: ContractServiceFee, description: str | None = None) -> str:
    """Build one-line PDF display for a service fee.

    RAO-P1-100: KISS redesign — "Tekst na umowie" (description) is the single source
    of truth for the printed line. Fallback to amount/unit only when description is empty.

    Placeholders $1/$2 are replaced with the formatted amount + zł so the PDF
    never contains a '$' sign.
    """
    name = (fee.name or "").strip()
    desc = (description or fee.description or "").strip()
    if desc:
        desc = _resolve_fee_description(desc, fee.amount_from, fee.amount_to)
        return f"- {name}: {desc}"
    amount_line = _build_fee_amount_line(fee)
    if amount_line:
        return f"- {name}: {amount_line}"
    return f"- {name}"


async def build_contract_data(db: AsyncSession, contract_id: int) -> dict:
    from sqlalchemy.orm import selectinload
    from contracts.service import format_position_conditions_cascading
    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.positions).selectinload(ContractPosition.machine),
            selectinload(Contract.service_fees),
        )
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        return {}

    contractor = await db.get(Contractor, contract.contractor_id)
    company = await db.get(Company, 1)
    salesperson = None
    if contract.salesperson_id:
        salesperson = await db.get(Salesperson, contract.salesperson_id)

    positions = contract.positions
    fees = contract.service_fees

    # RAO-P0-032: Nie mutuj obiektów sesji — buduj lokalne kopie description
    # RAO-P1-100: KISS redesign — description zawiera gotowy tekst do wydruku;
    # ewentualne placeholdery $1/$2 są rozwijane w _resolve_fee_description.
    fees_data = []
    for f in fees:
        desc = (f.description or "").strip()
        fees_data.append({
            "fee": f,
            "description": desc,
            "display": _format_fee_display(f, desc),
        })

    positions_data = []
    for pos in positions:
        conds_result = await db.execute(
            select(PositionCondition).where(PositionCondition.position_id == pos.id)
        )
        conditions = conds_result.scalars().all()
        rate_type = None
        if pos.rate_type_id:
            rate_type = await db.get(RateType, pos.rate_type_id)

        machine = await db.get(MachineModel, pos.machine_id) if pos.machine_id else None

        # Use new cascading formatter for conditions
        conditions_text = format_position_conditions_cascading(conditions, contract.contract_type)

        # Fetch service hours for this position
        # RAO-P1-014 (usunięte): service_hours table dropped — PDF fallback to empty list.
        # Formularz papierowy wypełniany ręcznie (5 pustych wierszy w template).
        service_hours = []

        positions_data.append({
            "pos": pos,
            "conditions": conditions,
            "conditions_text": conditions_text,
            "rate_type_name": rate_type.name if rate_type else None,
            "replacement_value": machine.replacement_value if machine else None,
            "serial_no": machine.serial_no if machine else None,
            "registration_no": machine.registration_no if machine else None,
            "service_hours": service_hours,
        })

    return {
        "contract": contract,
        "contractor": contractor,
        "company": company,
        "salesperson": salesperson,
        "positions": positions_data,
        "fees": fees_data,
        "fees_text": generate_fees_text(fees_data),
    }


async def generate_summary_pdf(db: AsyncSession, summary_type: str) -> bytes:
    import asyncio
    from sqlalchemy import select
    from contractors.models import Contractor
    from machines.models import Machine
    from markupsafe import escape as _esc

    if summary_type == "contractors":
        result = await db.execute(select(Contractor).order_by(Contractor.name))
        items = result.scalars().all()
        html = """<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:'Roboto',sans-serif;font-size:11px;color:#222;padding:20px;}
        h1{font-size:15px;color:#1D2B53;margin-bottom:12px;}
        table{width:100%;border-collapse:collapse;}
        th{background:#1D2B53;color:#fff;padding:5px 8px;text-align:left;font-size:10px;}
        td{padding:4px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}
        tr:nth-child(even) td{background:#f7f8ff;}</style></head><body>
        <h1>Zestawienie Kontrahentów</h1>
        <table><thead><tr><th>#</th><th>Nazwa</th><th>NIP</th><th>Miasto</th><th>Telefon</th><th>Email</th></tr></thead><tbody>"""
        for i, c in enumerate(items, 1):
            html += f"<tr><td>{i}</td><td>{_esc(c.name or '')}</td><td>{_esc(c.nip or '—')}</td><td>{_esc(c.city or '—')}</td><td>{_esc(c.phone1 or '—')}</td><td>{_esc(c.email or '—')}</td></tr>"
        html += "</tbody></table></body></html>"
    else:
        result = await db.execute(select(Machine).order_by(Machine.name))
        items = result.scalars().all()
        html = """<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:'Roboto',sans-serif;font-size:11px;color:#222;padding:20px;}
        h1{font-size:15px;color:#1D2B53;margin-bottom:12px;}
        table{width:100%;border-collapse:collapse;}
        th{background:#1D2B53;color:#fff;padding:5px 8px;text-align:left;font-size:10px;}
        td{padding:4px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}
        tr:nth-child(even) td{background:#f7f8ff;}</style></head><body>
        <h1>Zestawienie Maszyn</h1>
        <table><thead><tr><th>#</th><th>Nazwa</th><th>Nr wew.</th><th>Nr rej.</th><th>Marka/Model</th></tr></thead><tbody>"""
        for i, a in enumerate(items, 1):
            marka = f"{a.brand or ''} {a.model or ''}".strip() or "—"
            html += f"<tr><td>{i}</td><td>{_esc(a.name)}</td><td>{_esc(a.internal_number or '—')}</td><td>{_esc(a.registration_no or '—')}</td><td>{_esc(marka)}</td></tr>"
        html += "</tbody></table></body></html>"

    return await asyncio.get_event_loop().run_in_executor(None, _html_to_pdf_sync, html)


def _merge_pdfs(pdf_pages: list[bytes]) -> bytes:
    """Merge multiple PDF byte streams into one PDF.
    Uses pypdf if available, otherwise falls back to weasyprint concatenation.
    """
    try:
        from pypdf import PdfWriter
        import io
        writer = PdfWriter()
        for page_bytes in pdf_pages:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(page_bytes))
            for page in reader.pages:
                writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except ImportError:
        # Fallback: pypdf not available — return first page only (graceful degradation)
        # In production, pypdf should be installed: pip install pypdf
        return pdf_pages[0] if pdf_pages else b""


def _html_to_pdf_sync(html: str, use_playwright_footer: bool = True) -> bytes:
    """Render HTML to PDF. Renderer controlled by RAO_PDF_RENDERER env var.
    weasyprint (default) — identical output on dev and prod (shared hosting).
    playwright — Chromium-based, higher CSS fidelity, requires browser binaries.
    use_playwright_footer=False also signals protocol mode for WeasyPrint (no side margins).
    """
    from config import settings
    if settings.RAO_PDF_RENDERER == "playwright":
        return _pdf_via_playwright(html, use_playwright_footer)
    return _pdf_via_weasyprint(html, use_playwright_footer)


def _pdf_via_playwright(html: str, use_footer: bool = True) -> bytes:
    """Playwright/Chromium renderer — full-featured, requires browser binaries."""
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
        if use_footer:
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=footer_template,
                margin={"top": "0", "bottom": "15mm", "left": "0", "right": "0"}
            )
        else:
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                display_header_footer=False,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
            )
        browser.close()
    return pdf_bytes


_FONT_DIR = pathlib.Path(__file__).parent / "fonts"


def _font_face_css() -> str:
    """Build @font-face CSS pointing to bundled .ttf files.

    Bundled fonts (all in backend/reports/fonts/):
      Montserrat  — body/headers (Toolsmart design system)
      Tinos       — OWN legal sections (metrically identical to Times New Roman)
      Roboto      — page footer counters
    """
    def _uri(name: str) -> str:
        return (_FONT_DIR / name).resolve().as_posix()

    faces = []

    for name, weight, fname in [
        ("Montserrat", 400, "Montserrat-Regular.ttf"),
        ("Montserrat", 700, "Montserrat-Bold.ttf"),
        ("Tinos",      400, "Tinos-Regular.ttf"),
        ("Tinos",      700, "Tinos-Bold.ttf"),
        ("Roboto",     400, "Roboto-Regular.ttf"),
        ("Roboto",     700, "Roboto-Bold.ttf"),
    ]:
        path = _FONT_DIR / fname
        if not path.exists():
            continue
        faces.append(f"""
    @font-face {{
        font-family: '{name}';
        font-style: normal;
        font-weight: {weight};
        src: url('file:///{_uri(fname)}') format('truetype');
    }}""")

    return "\n".join(faces)


def _pdf_via_weasyprint(html: str, use_footer: bool = True) -> bytes:
    """WeasyPrint renderer — works on shared hosting without browser binaries.
    use_footer=False: protocol mode — no side/top page margins, only bottom for footer.
    """
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    import datetime

    font_config = FontConfiguration()
    now = datetime.datetime.now().strftime("%d.%m.%Y")

    font_face = _font_face_css()
    # Protocols declare their own internal padding; only need bottom margin for footer.
    # Contracts use generous margins for their layout.
    page_margin = "0 0 15mm 0" if not use_footer else "10mm 10mm 18mm 10mm"
    bottom_left_padding = "" if use_footer else "padding-left: 10mm;"
    bottom_right_padding = "" if use_footer else "padding-right: 10mm;"
    extra_css = f"""
    {font_face}
    @page {{
        size: A4;
        margin: {page_margin};
        @bottom-left  {{ content: "Wydrukowano {now}"; font-size: 8px; color: #444; font-family: 'Roboto', sans-serif; {bottom_left_padding} }}
        @bottom-right {{ content: "Strona " counter(page) " z " counter(pages); font-size: 8px; color: #444; font-family: 'Roboto', sans-serif; {bottom_right_padding} }}
    }}
    #footer-legal-running {{
        position: absolute;
        bottom: 0;
        left: 14mm;
        right: 14mm;
        font-size: 8px;
        line-height: 1.35;
        color: #000;
    }}
    """
    if "</head>" in html:
        html = html.replace("</head>", f"<style>{extra_css}</style></head>")
    else:
        html = f"<style>{extra_css}</style>{html}"
    import os
    assets_dir = os.path.join(os.path.dirname(__file__), "templates")
    return HTML(string=html, base_url=assets_dir).write_pdf(
        font_config=font_config,
        stylesheets=[CSS(string=font_face, font_config=font_config)] if font_face else [],
    )


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
        return formatted + ' z\u0142'
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


async def generate_commissions_pdf(db: AsyncSession, date_from: date, date_to: date) -> bytes:
    from stats.router import _compute_position_revenues, _contract_date_filter
    from markupsafe import escape as _esc
    import asyncio

    df, dt = date_from, date_to
    all_pos = await _compute_position_revenues(db, df, dt)

    sp_q = await db.execute(
        select(Salesperson.id, Salesperson.name, Salesperson.commission_rate)
        .where(Salesperson.is_active == True)
        .order_by(Salesperson.name)
    )
    salespeople = {r[0]: {"name": r[1], "rate": r[2]} for r in sp_q.all()}

    contract_sp_q = await db.execute(
        select(Contract.id, Contract.salesperson_id)
        .where(and_(*_contract_date_filter(df, dt)))
        .where(Contract.salesperson_id.isnot(None))
    )
    contract_sp_map = {r[0]: r[1] for r in contract_sp_q.all()}

    agg: dict = defaultdict(lambda: {"revenue": Decimal(0), "contracts": set()})
    for p in all_pos:
        sp_id = contract_sp_map.get(p["contract_id"])
        if sp_id and sp_id in salespeople:
            agg[sp_id]["revenue"] += p["revenue"]
            agg[sp_id]["contracts"].add(p["contract_id"])

    items = []
    for sp_id, sp_data in salespeople.items():
        data = agg.get(sp_id, {"revenue": Decimal(0), "contracts": set()})
        rate = sp_data["rate"] or Decimal(0)
        revenue = data["revenue"]
        commission = (revenue * rate / Decimal(100)).quantize(Decimal("0.01"))
        items.append({"name": sp_data["name"], "contracts_count": len(data["contracts"]),
                       "rate": rate, "revenue": revenue, "commission": commission})
    items.sort(key=lambda x: x["commission"], reverse=True)

    grand_revenue = sum(i["revenue"] for i in items)
    grand_commission = sum(i["commission"] for i in items)

    rows_html = "".join(
        f"<tr><td>{i}</td><td>{_esc(it['name'])}</td><td class='num'>{it['contracts_count']}</td>"
        f"<td class='num'>{it['rate'] if it['rate'] else '—'} %</td>"
        f"<td class='num'>{_fmt_money(it['revenue'])}</td>"
        f"<td class='num commission'>{_fmt_money(it['commission'])}</td></tr>"
        for i, it in enumerate(items, 1)
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{font-family:'Roboto',sans-serif;font-size:11px;color:#222;padding:20px;}}
h1{{font-size:16px;color:#1D2B53;margin-bottom:4px;}}
.period{{font-size:11px;color:#666;margin-bottom:16px;}}
.summary{{display:flex;gap:24px;margin-bottom:20px;}}
.kpi{{background:#f7f8ff;border:1px solid #e0e4ef;border-radius:6px;padding:10px 18px;}}
.kpi-label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px;}}
.kpi-value{{font-size:18px;font-weight:700;color:#1D2B53;}}
table{{width:100%;border-collapse:collapse;}}
th{{background:#1D2B53;color:#fff;padding:6px 8px;text-align:left;font-size:10px;}}
th.num,td.num{{text-align:right;}}
td{{padding:5px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}}
tr:nth-child(even) td{{background:#f7f8ff;}}
tfoot td{{background:#e8ecf8;font-weight:700;border-top:2px solid #1D2B53;}}
td.commission{{color:#27ae60;font-weight:600;}}
</style></head><body>
<h1>Raport prowizji handlowców</h1>
<p class="period">Okres: {df.strftime('%d.%m.%Y')} — {dt.strftime('%d.%m.%Y')}</p>
<div class="summary">
  <div class="kpi"><div class="kpi-label">Łączny przychód</div><div class="kpi-value">{_fmt_money(grand_revenue)}</div></div>
  <div class="kpi"><div class="kpi-label">Łączna prowizja</div><div class="kpi-value">{_fmt_money(grand_commission)}</div></div>
</div>
<table>
<thead><tr><th>#</th><th>Handlowiec</th><th class="num">Umów</th><th class="num">Stawka prowizji</th><th class="num">Przychód</th><th class="num">Prowizja</th></tr></thead>
<tbody>{rows_html}</tbody>
<tfoot><tr><td colspan="4"><strong>RAZEM</strong></td><td class="num">{_fmt_money(grand_revenue)}</td><td class="num commission">{_fmt_money(grand_commission)}</td></tr></tfoot>
</table>
</body></html>"""

    return await asyncio.get_event_loop().run_in_executor(None, _html_to_pdf_sync, html)


async def generate_stats_pdf(db: AsyncSession, date_from: date, date_to: date) -> bytes:
    from stats.router import _compute_position_revenues, _contract_date_filter
    from machines.models import Machine
    from markupsafe import escape as _esc
    import asyncio

    df, dt = date_from, date_to
    today = date.today()

    all_pos = await _compute_position_revenues(db, df, dt)

    # Fleet summary
    total_q = await db.execute(select(func.count()).select_from(Machine))
    total_machines = total_q.scalar() or 0
    rented_q = await db.execute(
        select(func.count(func.distinct(ContractPosition.machine_id)))
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Machine, Machine.id == ContractPosition.machine_id)
        .where(and_(Contract.date_from <= today, Contract.date_to >= today))
    )
    total_rented = rented_q.scalar() or 0
    util_pct = round((total_rented / total_machines * 100) if total_machines else 0, 1)
    period_revenue = sum(p["revenue"] for p in all_pos)

    cnt_q = await db.execute(
        select(func.count()).select_from(Contract)
        .where(and_(*_contract_date_filter(df, dt)))
    )
    contracts_in_period = cnt_q.scalar() or 0

    # Top machines
    machine_agg: dict = defaultdict(lambda: {"name": "", "internal_number": None, "revenue": Decimal(0), "days": 0, "contracts": set()})
    for p in all_pos:
        if not p["is_service"]:
            k = p["machine_id"]
            machine_agg[k]["name"] = p["machine_name"]
            machine_agg[k]["internal_number"] = p["internal_number"]
            machine_agg[k]["revenue"] += p["revenue"]
            machine_agg[k]["days"] += p["clamped_days"]
            machine_agg[k]["contracts"].add(p["contract_id"])
    top10 = sorted(machine_agg.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10]

    # Services breakdown — RAO: separacja usług zwykłych od dodatkowych
    svc_agg: dict = defaultdict(lambda: {"name": "", "revenue": Decimal(0), "contracts": set()})
    for p in all_pos:
        if p.get("is_additional_service"):
            # Usługi dodatkowe — klucz po additional_service_id (nie service_id — kolizja ID)
            k = ("addl", p.get("additional_service_id"))
            svc_agg[k]["name"] = p["service_name"]
            svc_agg[k]["revenue"] += p["revenue"]
            svc_agg[k]["contracts"].add(p["contract_id"])
        elif p["is_service"]:
            # Usługi zwykłe — klucz po service_id (Service.id)
            k = ("svc", p["service_id"])
            svc_agg[k]["name"] = p["service_name"]
            svc_agg[k]["revenue"] += p["revenue"]
            svc_agg[k]["contracts"].add(p["contract_id"])
    svc_sorted = sorted(svc_agg.items(), key=lambda x: x[1]["revenue"], reverse=True)

    # Locations
    contractor_ids = set(p["contractor_id"] for p in all_pos if p["contractor_id"])
    city_map = {}
    if contractor_ids:
        city_q = await db.execute(
            select(Contractor.id, Contractor.city)
            .where(and_(Contractor.id.in_(contractor_ids), Contractor.city.isnot(None), Contractor.city != ""))
        )
        city_map = {r[0]: r[1] for r in city_q.all()}
    loc_agg: dict = defaultdict(lambda: {"cnt": 0, "rev": Decimal(0), "contracts": set()})
    for p in all_pos:
        city = city_map.get(p["contractor_id"])
        if city:
            loc_agg[city]["rev"] += p["revenue"]
            loc_agg[city]["contracts"].add(p["contract_id"])
    for city, d in loc_agg.items():
        d["cnt"] = len(d["contracts"])
    top_locations = sorted(loc_agg.items(), key=lambda x: x[1]["cnt"], reverse=True)[:15]

    # Build HTML sections
    top10_rows = "".join(
        f"<tr><td>{i}</td><td>{_esc(d['name'])}</td><td class='num'>{_esc(d['internal_number'] or '—')}</td>"
        f"<td class='num'>{d['days']}</td><td class='num'>{len(d['contracts'])}</td>"
        f"<td class='num'><strong>{_fmt_money(d['revenue'])}</strong></td></tr>"
        for i, (_, d) in enumerate(top10, 1)
    )
    svc_rows = "".join(
        f"<tr><td>{i}</td><td>{_esc(d['name'])}</td><td class='num'>{len(d['contracts'])}</td>"
        f"<td class='num'><strong>{_fmt_money(d['revenue'])}</strong></td></tr>"
        for i, (_, d) in enumerate(svc_sorted, 1)
    ) or "<tr><td colspan='4' class='empty'>Brak danych</td></tr>"
    loc_rows = "".join(
        f"<tr><td>{i}</td><td>{_esc(city)}</td><td class='num'>{d['cnt']}</td>"
        f"<td class='num'>{_fmt_money(d['rev'])}</td></tr>"
        for i, (city, d) in enumerate(top_locations, 1)
    ) or "<tr><td colspan='4' class='empty'>Brak danych</td></tr>"

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{font-family:'Roboto',sans-serif;font-size:11px;color:#222;padding:20px;}}
h1{{font-size:17px;color:#1D2B53;margin-bottom:4px;}}
h2{{font-size:13px;color:#1D2B53;margin:18px 0 8px;border-bottom:2px solid #1D2B53;padding-bottom:4px;}}
.period{{font-size:11px;color:#666;margin-bottom:16px;}}
.kpi-row{{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;}}
.kpi{{background:#f7f8ff;border:1px solid #e0e4ef;border-radius:6px;padding:10px 18px;min-width:130px;}}
.kpi-label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px;}}
.kpi-value{{font-size:18px;font-weight:700;color:#1D2B53;}}
table{{width:100%;border-collapse:collapse;margin-bottom:4px;}}
th{{background:#1D2B53;color:#fff;padding:6px 8px;text-align:left;font-size:10px;}}
th.num,td.num{{text-align:right;}}
td{{padding:5px 8px;border-bottom:1px solid #e2e8f0;font-size:10px;}}
tr:nth-child(even) td{{background:#f7f8ff;}}
td.empty{{color:#aaa;text-align:center;padding:12px;}}
</style></head><body>
<h1>Raport statystyk — {df.strftime('%d.%m.%Y')} – {dt.strftime('%d.%m.%Y')}</h1>

<div class="kpi-row">
  <div class="kpi"><div class="kpi-label">Wynajętych maszyn</div><div class="kpi-value">{total_rented} / {total_machines}</div></div>
  <div class="kpi"><div class="kpi-label">Wykorzystanie floty</div><div class="kpi-value">{util_pct}%</div></div>
  <div class="kpi"><div class="kpi-label">Przychód w okresie</div><div class="kpi-value">{_fmt_money(period_revenue)}</div></div>
  <div class="kpi"><div class="kpi-label">Umów w okresie</div><div class="kpi-value">{contracts_in_period}</div></div>
</div>

<h2>TOP 10 Maszyn wg przychodu</h2>
<table>
<thead><tr><th>#</th><th>Maszyna</th><th class="num">Nr wew.</th><th class="num">Dni</th><th class="num">Umów</th><th class="num">Przychód</th></tr></thead>
<tbody>{top10_rows}</tbody>
</table>

<h2>Usługi dodatkowe</h2>
<table>
<thead><tr><th>#</th><th>Usługa</th><th class="num">Umów</th><th class="num">Przychód</th></tr></thead>
<tbody>{svc_rows}</tbody>
</table>

<h2>Lokalizacje — ranking</h2>
<table>
<thead><tr><th>#</th><th>Miasto</th><th class="num">Umów</th><th class="num">Przychód</th></tr></thead>
<tbody>{loc_rows}</tbody>
</table>
</body></html>"""

    return await asyncio.get_event_loop().run_in_executor(None, _html_to_pdf_sync, html)


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
    # RAO-P0-031: autoescape=True chroni przed XSS/HTML injection z danych DB
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )
    env.filters['datepl'] = _fmt_date_pl
    env.filters['money'] = _fmt_money
    env.filters['money_plain'] = _fmt_money_plain

    try:
        template = env.get_template(template_name)
    except Exception:
        template = env.get_template("contract.html")

    from datetime import datetime
    import base64
    data["now"] = datetime.now().strftime("%d.%m.%Y")

    # Stamp as base64 data URI — portable across renderers and machines
    _stamp_path = pathlib.Path(__file__).parent / "assets" / "protocol_stamp.png"
    if _stamp_path.exists():
        with open(_stamp_path, "rb") as _f:
            data["stamp_src"] = "data:image/png;base64," + base64.b64encode(_f.read()).decode()
    else:
        data["stamp_src"] = ""

    is_protocol = report_type.startswith("protocol_")

    # P1-011: Oddzielny protokół per maszyna w jednym PDF
    # Każda strona = pełny protokół z jedną pozycją
    # Stopka: "Protokół X z Y" zamiast "Strona X z Y"
    if is_protocol:
        positions = data.get("positions", [])
        if not positions:
            # Brak pozycji — renderuj jeden pusty protokół (zgodnie z dotychczasowym zachowaniem)
            data["protocol_number"] = 1
            data["protocol_total"] = 1
            data["positions"] = positions  # pusta lista
            html = template.render(**data)
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                None, _html_to_pdf_sync, html, not is_protocol
            )
            return pdf_bytes

        # Renderuj osobny protokół per pozycja, połącz w jeden PDF
        pdf_pages = []
        total = len(positions)
        loop = asyncio.get_event_loop()
        for idx, pos in enumerate(positions, 1):
            page_data = dict(data)
            page_data["positions"] = [pos]  # tylko ta jedna pozycja
            page_data["protocol_number"] = idx
            page_data["protocol_total"] = total
            html = template.render(**page_data)
            page_pdf = await loop.run_in_executor(
                None, _html_to_pdf_sync, html, not is_protocol
            )
            pdf_pages.append(page_pdf)

        # Połącz wszystkie strony w jeden PDF
        if len(pdf_pages) == 1:
            return pdf_pages[0]
        return _merge_pdfs(pdf_pages)

    html = template.render(**data)
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _html_to_pdf_sync, html, not is_protocol
    )
    return pdf_bytes
