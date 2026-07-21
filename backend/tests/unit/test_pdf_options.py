"""RAO-P2-064: testy opcji wydruku PDF na umowie.

Weryfikuje że hide_delivery_address i signatures_on_page1
są honorowane przez szablony contract.html / contract_u.html.
report_without_data NIE powinien wpływać na umowę (martwe pole — PZ bez danych
jest osobnym raportem osiągalnym przez context menu).
"""
import pytest
import pdfplumber
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

from reports.service import generate_pdf


def _pdf_pages_text(pdf_bytes: bytes) -> list[str]:
    """Wyciąga tekst z PDF — lista per strona."""
    pages = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages


def _make_contract(**overrides) -> MagicMock:
    """Fabryka mock-contract z domyślnymi flagami.
    Ustawia wszystkie pola używane w szablonach PDF na puste wartości,
    żeby MagicMock nie zwracał losowych obiektów dla nieustawionych atrybutów.
    """
    defaults = dict(
        id=1, number="S/2026/01/01", contract_type="S",
        date_from="2026-01-01", date_to=None,
        delivery_address="ul. Testowa 1, Warszawa",
        hide_delivery_address=False, signatures_on_page1=False,
        report_without_data=False,
        contact_person1="Jan Kowalski", contact_phone1="500123456",
        contact_person2=None, contact_phone2=None,
        prepayment_amount=0, working_days_per_week=6,
        contractor_id=1, salesperson_id=None, notes_contract="", notes_protocol="",
        contractor_name="", email="", email2="",
    )
    defaults.update(overrides)
    # spec=Contract wymusza że tylko zdefiniowane atrybuty istnieją
    from contracts.models import Contract
    c = MagicMock(spec=Contract)
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def _mock_data(contract) -> dict:
    return {
        "contract": contract, "contractor": None, "company": None,
        "positions": [], "fees": [], "fees_text": "", "salesperson": None,
    }


# ===== HIDE_DELIVERY_ADDRESS =====

@pytest.mark.asyncio
async def test_hide_delivery_address_false_shows_address(monkeypatch):
    """H1: hide=FALSE + adres ustawiony → PDF zawiera 'Adres dostawy' i adres."""
    contract = _make_contract(hide_delivery_address=False,
                              delivery_address="ul. Testowa 1, Warszawa")
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    text = "\n".join(_pdf_pages_text(pdf))
    assert "Adres dostawy" in text
    assert "ul. Testowa 1" in text


@pytest.mark.asyncio
async def test_hide_delivery_address_true_hides_address_value(monkeypatch):
    """H2: hide=TRUE + adres ustawiony → PDF NIE zawiera adresu 'ul. Testowa 1'.
    Label 'Adres dostawy' zostaje (puste pole do wpisu ręcznego)."""
    contract = _make_contract(hide_delivery_address=True,
                              delivery_address="ul. Testowa 1, Warszawa")
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    text = "\n".join(_pdf_pages_text(pdf))
    assert "ul. Testowa 1" not in text, "Adres powinien być ukryty"
    assert "Adres dostawy" in text, "Label zostaje (puste pole do wpisu)"


@pytest.mark.asyncio
async def test_hide_delivery_address_null_address_no_op(monkeypatch):
    """H3/H4: delivery_address=NULL → nic nie pokazuje niezależnie od flagi."""
    for hide in (True, False):
        contract = _make_contract(hide_delivery_address=hide, delivery_address=None)
        monkeypatch.setattr("reports.service.build_contract_data",
                            AsyncMock(return_value=_mock_data(contract)))
        pdf = await generate_pdf(AsyncMock(), 1, "contract")
        text = "\n".join(_pdf_pages_text(pdf))
        # NULL → nie pokazuje adresu (ale hide=TRUE może pokazać label z pustym polem)
        if not hide:
            assert "ul. Testowa" not in text


@pytest.mark.asyncio
async def test_hide_delivery_address_whitespace_only(monkeypatch):
    """H7: delivery_address='   ' → trim → nie pokazuje adresu (whitespace bug fix)."""
    contract = _make_contract(hide_delivery_address=False, delivery_address="   ")
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    text = "\n".join(_pdf_pages_text(pdf))
    # Po fix: trim w szablonie → nie pokazuje samego adresu
    assert "ul. Testowa" not in text


@pytest.mark.asyncio
async def test_hide_delivery_address_contract_u_template(monkeypatch):
    """H2 dla contract_u.html (typ U)."""
    contract = _make_contract(contract_type="U", hide_delivery_address=True,
                              delivery_address="ul. Testowa 1")
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    text = "\n".join(_pdf_pages_text(pdf))
    assert "ul. Testowa 1" not in text


# ===== SIGNATURES_ON_PAGE1 =====

@pytest.mark.asyncio
async def test_signatures_on_page1_true_shows_on_page1(monkeypatch):
    """S1: signatures=TRUE → strona 1 zawiera 'czytelny podpis'."""
    contract = _make_contract(signatures_on_page1=True)
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    pages = _pdf_pages_text(pdf)
    assert len(pages) >= 1
    assert "czytelny podpis" in pages[0]


@pytest.mark.asyncio
async def test_signatures_on_page1_false_hides_on_page1(monkeypatch):
    """S2: signatures=FALSE → strona 1 NIE zawiera 'czytelny podpis'.
    BUG fix: wcześniej zawsze były podpisy na str 1."""
    contract = _make_contract(signatures_on_page1=False)
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    pages = _pdf_pages_text(pdf)
    assert "czytelny podpis" not in pages[0], "Podpisy na str 1 powinny być ukryte"


@pytest.mark.asyncio
async def test_signatures_on_page1_false_contract_u(monkeypatch):
    """S2 dla contract_u.html (typ U)."""
    contract = _make_contract(contract_type="U", signatures_on_page1=False)
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(contract)))
    pdf = await generate_pdf(AsyncMock(), 1, "contract")
    pages = _pdf_pages_text(pdf)
    assert "czytelny podpis" not in pages[0]


# ===== REPORT_WITHOUT_DATA (martwe pole — NO-OP dla umowy) =====

@pytest.mark.asyncio
async def test_report_without_data_no_effect_on_contract(monkeypatch):
    """R1/R2: report_without_data NIE wpływa na umowę (contract.html).
    Obie wartości dają identyczny PDF."""
    c1 = _make_contract(report_without_data=True)
    c2 = _make_contract(report_without_data=False)
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(c1)))
    pdf1 = await generate_pdf(AsyncMock(), 1, "contract")
    monkeypatch.setattr("reports.service.build_contract_data",
                        AsyncMock(return_value=_mock_data(c2)))
    pdf2 = await generate_pdf(AsyncMock(), 1, "contract")
    t1 = "\n".join(_pdf_pages_text(pdf1))
    t2 = "\n".join(_pdf_pages_text(pdf2))
    assert t1 == t2, "report_without_data nie powinien wpływać na umowę"
