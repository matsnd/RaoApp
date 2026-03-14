from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contractors.models import Contractor
from settings.models import Company, Salesperson, RateType


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
        positions_data.append({
            "pos": pos,
            "conditions": conditions,
            "rate_type_name": rate_type.name if rate_type else None,
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


async def generate_pdf(db: AsyncSession, contract_id: int, report_type: str = "contract") -> bytes:
    from jinja2 import Environment, FileSystemLoader
    import os
    import weasyprint

    data = await build_contract_data(db, contract_id)
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))

    template_map = {
        "contract": "contract.html",
        "protocol_zo": "protocol_zo.html",
        "protocol_zo_nodata": "protocol_zo_nodata.html",
    }
    template_name = template_map.get(report_type, "contract.html")

    try:
        template = env.get_template(template_name)
    except Exception:
        template = env.get_template("contract.html")

    html = template.render(**data)
    pdf = weasyprint.HTML(string=html).write_pdf()
    return pdf
