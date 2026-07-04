import asyncio, sys
sys.path.insert(0, '.')
from unittest.mock import AsyncMock, MagicMock
from reports.service import generate_pdf
import pdfplumber
from io import BytesIO

def _pages(pdf_bytes):
    pages = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages

def _make(**ov):
    d = dict(id=1, number="S/2026/01/01", contract_type="S", date_from="2026-01-01",
             date_to=None, delivery_address="ul. Testowa 1, Warszawa",
             hide_delivery_address=False, signatures_on_page1=False, report_without_data=False,
             contact_person1="Jan", contact_phone1="500", contact_person2=None, contact_phone2=None,
             prepayment_amount=0, working_days_per_week=6, contractor_id=1, salesperson_id=None, notes="")
    d.update(ov)
    c = MagicMock()
    for k,v in d.items(): setattr(c, k, v)
    return c

def _data(c): return {"contract": c, "contractor": None, "company": None, "positions": [], "fees": [], "fees_text": "", "salesperson": None}

async def main():
    import reports.service as svc
    c1 = _make(report_without_data=True)
    c2 = _make(report_without_data=False)
    svc.build_contract_data = AsyncMock(return_value=_data(c1))
    pdf1 = await generate_pdf(AsyncMock(), 1, "contract")
    svc.build_contract_data = AsyncMock(return_value=_data(c2))
    pdf2 = await generate_pdf(AsyncMock(), 1, "contract")
    t1 = _pages(pdf1)
    t2 = _pages(pdf2)
    print("pages1:", len(t1), "pages2:", len(t2))
    for i,(p1,p2) in enumerate(zip(t1,t2)):
        if p1 != p2:
            print(f"PAGE {i} DIFFERS")
            lines1 = p1.split('\n')
            lines2 = p2.split('\n')
            for j,(l1,l2) in enumerate(zip(lines1,lines2)):
                if l1 != l2:
                    print(f"  line {j}: [{l1!r}] vs [{l2!r}]")
            # extra lines
            if len(lines1) != len(lines2):
                print(f"  line count: {len(lines1)} vs {len(lines2)}")
                extra = lines1[len(lines2):] if len(lines1)>len(lines2) else lines2[len(lines1):]
                print(f"  extra: {extra!r}")
            break
    else:
        print("IDENTICAL")

asyncio.run(main())
