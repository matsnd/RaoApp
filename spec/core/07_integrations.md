# 07 — Integracje zewnętrzne

> **INSTRUKCJA DLA AGENTA:** Implementuj te integracje dokładnie jak opisane.
> Żadnych procedur składowanych — cała logika w Python (SQLAlchemy ORM).

## 1. GUS REGON BIR1 API (SOAP)

### Kiedy używane
Przycisk `[GUS]` w formularzu kontrahenta → auto-fill danych firmy po NIP.

### Endpoint
`POST /integrations/gus-lookup`

### Konfiguracja
```env
RAO_GUS_API_KEY=abcdefghijklmnop    # Klucz API z stat.gov.pl
```

Produkcyjny WSDL: `https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc`
Testowy WSDL: `https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc`

### Status integracji (2026-05-22)

**Current state:** WORKING ✅
- Klucz GUS ze starej aplikacji (d4feaf84608747c1addd) działa poprawnie
- Login zwraca session ID (potwierdzone: `u78py7m9v4nc68eu2x8d`)
- Metoda wyszukiwania: `DaneSzukaj` (z biblioteki gusregon)
- Endpoint: Production GUS API (wyszukiwarkaregon.stat.gov.pl)
- MTOM/XOP response handling: implemented (extracts XML from multipart)
- Fallback do pełnego raportu: implemented (BIR11OsPrawna)

**Testowane NIP-y:**
- `5250008455`, `5211112460`, `5213305298` → ErrorCode 4 (nie istnieją w bazie GUS)
- Użyj prawdziwych NIP-ów z aktywnych firm

**Implementacja:** `backend/integrations/gus.py` — pełna implementacja SOAP

### Implementacja SOAP (aktualna)

```python
# integrations/gus.py (pełna wersja SOAP)
import httpx
from config import settings
from lxml import etree

# Production URL (from old app)
# Note: Test endpoint (wyszukiwarkaregontest) requires different API key
# This production endpoint works with current API key
GUS_WSDL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"

def _build_envelope(action: str, body_content: str) -> str:
    return (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
        f'<soap:Header><wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">{GUS_WSDL}</wsa:To>'
        f'<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">{action}</wsa:Action>'
        f'</soap:Header>'
        f'<soap:Body>{body_content}</soap:Body>'
        f'</soap:Envelope>'
    )

class GusClient:
    def __init__(self):
        self.api_key = settings.RAO_GUS_API_KEY
        self.sid: str | None = None

    async def lookup(self, nip: str) -> dict:
        """
        Lookup company data from GUS (Polish Central Statistical Office) by NIP.
        
        Integration status: WORKING
        - API key authentication: ✅ (login returns session ID)
        - Search method: DaneSzukaj (from gusregon library reference)
        - Endpoint: Production GUS API (wyszukiwarkaregon.stat.gov.pl)
        
        Note: Test NIPs (5250008455, 5211112460, 5213305298) return ErrorCode 4
        because they don't exist in GUS database. Use real NIPs from active companies.
        """
        from contractors.schemas import GusLookupResponse
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                self.sid = await self._login(client)
                if not self.sid:
                    return GusLookupResponse(
                        name=None, street=None, building_number=None, apartment_number=None,
                        postal_code=None, city=None, regon=None, province=None,
                        county=None, community=None, status="Błąd logowania: brak sesji",
                    )
                try:
                    result = await self._search(client, nip)
                    return GusLookupResponse(
                        name=result.get("Nazwa"),
                        street=result.get("Ulica"),
                        building_number=result.get("NrNieruchomosci"),
                        apartment_number=result.get("NrLokalu"),
                        postal_code=result.get("KodPocztowy"),
                        city=result.get("Miejscowosc"),
                        regon=result.get("Regon"),
                        province=result.get("Wojewodztwo"),
                        county=result.get("Powiat"),
                        community=result.get("Gmina"),
                        status=result.get("StatusNip"),
                    )
                finally:
                    await self._logout(client)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return GusLookupResponse(
                name=None, street=None, building_number=None, apartment_number=None,
                postal_code=None, city=None, regon=None, province=None,
                county=None, community=None, status=f"Błąd: {str(e)}",
            )

    async def _login(self, client: httpx.AsyncClient) -> str:
        body = f'<ns:Zaloguj xmlns:ns="http://CIS/BIR/PUBL/2014/07"><ns:pKluczUzytkownika>{self.api_key}</ns:pKluczUzytkownika></ns:Zaloguj>'
        resp = await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj", body),
            headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        
        # Handle MTOM/XOP response - extract XML from multipart
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)

        tree = etree.fromstring(content.encode())
        sid = tree.find(".//{http://CIS/BIR/PUBL/2014/07}ZalogujResult")
        sid_text = sid.text if sid is not None else ""
        return sid_text

    async def _search(self, client: httpx.AsyncClient, nip: str) -> dict:
        # Try NIP search using DaneSzukaj method (from gusregon library)
        body = (
            f'<ns:DaneSzukaj xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pParametryWyszukiwania>'
            f'<dat:Nip xmlns:dat="http://CIS/BIR/2014/07/DataContract">{nip}</dat:Nip>'
            f'</ns:pParametryWyszukiwania>'
            f'</ns:DaneSzukaj>'
        )
        headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
        if self.sid:
            headers["sid"] = self.sid

        resp = await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukaj", body),
            headers=headers)

        # Handle MTOM/XOP response - extract XML from multipart
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)

        # Parse response — XML embedded in CDATA
        tree = etree.fromstring(content.encode())
        result_el = tree.find(".//{http://CIS/BIR/PUBL/2014/07}DaneSzukajResult")
        if result_el is None:
            return {}
        if not result_el.text:
            # Try full report instead
            return await self._get_full_report(client, nip)
        inner = etree.fromstring(result_el.text.encode())
        dane = inner.find(".//dane")
        if dane is None:
            return {}
        result = {child.tag: child.text for child in dane}
        return result

    async def _get_full_report(self, client: httpx.AsyncClient, nip: str) -> dict:
        body = (
            f'<ns:DanePobierzPelnyRaport xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pParametryRaportu>'
            f'<dat:Nip xmlns:dat="http://CIS/BIR/2014/07/DataContract">{nip}</dat:Nip>'
            f'</ns:pParametryRaportu>'
            f'<ns:pNazwaRaportu>BIR11OsPrawna</ns:pNazwaRaportu>'
            f'</ns:DanePobierzPelnyRaport>'
        )
        headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
        if self.sid:
            headers["sid"] = self.sid

        resp = await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DanePobierzPelnyRaport", body),
            headers=headers)

        # Handle MTOM/XOP response
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)

        # Parse response
        tree = etree.fromstring(content.encode())
        result_el = tree.find(".//{http://CIS/BIR/PUBL/2014/07}DanePobierzPelnyRaportResult")
        if result_el is None or not result_el.text:
            return {}
        
        # Parse full report XML
        try:
            inner = etree.fromstring(result_el.text.encode())
            dane = inner.find(".//dane")
            if dane is None:
                return {}
            result = {child.tag: child.text for child in dane}
            return result
        except Exception as e:
            return {}

    async def _logout(self, client: httpx.AsyncClient):
        body = f'<ns:Wyloguj xmlns:ns="http://CIS/BIR/PUBL/2014/07"><ns:pIdentyfikatorSesji>{self.sid}</ns:pIdentyfikatorSesji></ns:Wyloguj>'
        await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj", body),
            headers={"Content-Type": "application/soap+xml; charset=utf-8"})

gus_client = GusClient()
```

---

## 2. Nominatim (Reverse Geocoding)

### Kiedy używane
Przycisk `[>>]` w formularzu umowy → po wpisaniu współrzędnych GPS → pobierz adres.

### Endpoint
`POST /integrations/reverse-geocode`

### Implementacja

```python
# integrations/nominatim.py
import httpx
from decimal import Decimal

class NominatimClient:
    BASE_URL = "https://nominatim.openstreetmap.org"
    HEADERS = {
        "User-Agent": "RAO-App/1.0 (equipment-rental-management)",
        "Accept-Language": "pl"
    }

    async def reverse_geocode(self, lat: Decimal, lng: Decimal) -> dict:
        """
        Pobiera adres na podstawie współrzędnych GPS.
        Rate limit: max 1 request/sekunda (Nominatim policy).
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/reverse",
                params={
                    "lat": str(lat),
                    "lon": str(lng),
                    "format": "json",
                    "addressdetails": "1",
                    "accept-language": "pl",
                },
                headers=self.HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
            address = data.get("address", {})

            return {
                "street": address.get("road"),
                "house_number": address.get("house_number"),
                "postal_code": address.get("postcode"),
                "hamlet": address.get("hamlet"),
                "city": address.get("city"),
                "town": address.get("town"),
                "village": address.get("village"),
                "county": address.get("county"),        # powiat
                "municipality": address.get("municipality"),  # gmina
                "province": address.get("state"),       # województwo
                "district": address.get("suburb") or address.get("city_district"),
                "neighbourhood": address.get("neighbourhood"),
                "display_name": data.get("display_name"),
            }
```

### Forward Geocoding (RAO-P2-005)

**Kiedy używane:**
Przycisk `[>>geo]` w formularzu umowy → po wybraniu adresu dostawy → pobierz współrzędne GPS.

**Endpoint:**
`POST /integrations/geocode`

**Implementacja:**
- Frontend: `ContractFormView.vue` — `onAddressSelect()` wywołuje endpoint po wyborze adresu z listy
- Backend: `POST /integrations/geocode` (forward geocoding) w `integrations/router.py`
- Wynik: latitude/longitude zapisywane do formularza (form object)
- Rate limit: max 1 request/sekunda (Nominatim policy)

---

## 2.5. GUS TERYT - Kody pocztowe (RAO-P2-015)

### Kiedy używane
Auto-uzupełnianie miasta po kodzie pocztowym w formularzach (kontrahenci, umowy).

### Endpointy
- `GET /integrations/postal-codes/{code}` — zwraca miasto dla kodu pocztowego
- `POST /integrations/teryt/sync` — synchronizuje słownik kodów pocztowych z pliku SQL

### Implementacja

**Źródło danych:**
- Development: 200+ kodów pocztowych z głównych miast (Warszawa, Kraków, Wrocław, Poznań, Gdańsk, Łódź, Katowice)
- Generacja: `backend/integrations/teryt/fetch_postal_codes.py`
- SQL: `backend/integrations/teryt/postal_codes_inserts.sql`

**Endpoint GET /integrations/postal-codes/{code}:**
```python
@router.get("/postal-codes/{code}", response_model=PostalCodeLookupResponse)
async def lookup_postal_code(code: str, _: User = Depends(get_current_user)):
    """Lookup city by postal code from dictionary (RAO-P1-008, RAO-P2-015)."""
    import re
    if not re.match(r"^\d{2}-\d{3}$", code):
        raise HTTPException(status_code=422, detail="Invalid postal code format. Expected XX-XXX")

    async with AsyncSessionLocal() as db:
        from integrations.models import PostalCode
        result = await db.execute(
            select(PostalCode).where(PostalCode.postal_code == code).limit(1)
        )
        postal = result.scalar_one_or_none()
        if not postal:
            raise HTTPException(status_code=404, detail="Postal code not found in dictionary")
        return PostalCodeLookupResponse(
            code=postal.postal_code,
            city=postal.city,
            voivodeship=postal.wojewodztwo,
        )
```

**Endpoint POST /integrations/teryt/sync:**
```python
@router.post("/teryt/sync", response_model=TerytSyncResponse)
async def sync_teryt_data(_: User = Depends(get_current_user)):
    """Sync postal codes from pre-generated SQL inserts (RAO-P2-015)."""
    import os
    import sqlalchemy as sa

    sql_file = os.path.join(os.path.dirname(__file__), "teryt", "postal_codes_inserts.sql")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    async with AsyncSessionLocal() as db:
        await db.execute(sa.text("DELETE FROM postal_codes"))
        await db.execute(sa.text(sql_content))
        await db.commit()

        result = await db.execute(sa.text("SELECT COUNT(*) FROM postal_codes"))
        count = result.scalar()
        return TerytSyncResponse(success=True, message=f"Synced {count} postal codes", count=count)
```

**Frontend integration:**
```vue
<!-- ContractorFormView.vue lub ContractFormView.vue -->
<input v-model="form.postal_code" @blur="onPostalCodeBlur" />

<script setup lang="ts">
const onPostalCodeBlur = async () => {
  if (/^\d{2}-\d{3}$/.test(form.postal_code)) {
    const response = await api.get(`/integrations/postal-codes/${form.postal_code}`)
    if (response.data.city) {
      form.city = response.data.city
    }
  }
}
</script>
```

**Uwagi:**
- Pełna baza kodów pocztowych Polski (~20k) wymaga rejestracji w GUS TERYT (teryt_ws1@stat.gov.pl)
- Developmentowa baza 200+ kodów wystarcza do testów i developmentu
- W produkcji można rozszerzyć do pełnej bazy przez GUS TERYT API lub zakup komercyjnej bazy

---

## 3. Raporty PDF (WeasyPrint + Jinja2)

### Kiedy używane
Context menu na umowie → "Wydruk → Umowa" / "Protokół ZO" / "Protokół ZO bez danych".

### Typy raportów

| Typ | Template | Dane |
|-----|----------|------|
| `contract` | `contract.html` | Pełna umowa z pozycjami, warunkami, adresem, opłatami |
| `protocol_zo` | `protocol_zo.html` | Protokół zdawczo-odbiorczy z danymi maszyn |
| `protocol_zo_nodata` | `protocol_zo_nodata.html` | Protokół ZO z pustymi polami do ręcznego wypełnienia |

### Implementacja

```python
# reports/service.py
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

class ReportService:
    def __init__(self, template_dir: str = "reports/templates"):
        self.jinja = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
        )

    async def generate_contract_pdf(
        self,
        db: AsyncSession,
        contract_id: int,
        report_type: str,
        output_dir: str,
    ) -> Path:
        """
        Generuje PDF dla umowy.

        Dane potrzebne do szablonu:
        - company: dane firmy (nagłówek, logo, NIP, adres, bank)
        - contract: dane umowy
        - contractor: dane kontrahenta
        - positions: pozycje z warunkami
        - fees: opłaty dodatkowe (tekst)
        """
        # 1. Pobierz dane
        contract = await self._get_contract_data(db, contract_id)
        company = await self._get_company_data(db)

        # 2. Wybierz template
        template_map = {
            "contract": "contract.html",
            "protocol_zo": "protocol_zo.html",
            "protocol_zo_nodata": "protocol_zo_nodata.html",
        }
        template = self.jinja.get_template(template_map[report_type])

        # 3. Render HTML
        html_content = template.render(
            company=company,
            contract=contract,
            positions=contract["positions"],
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # 4. Generate PDF
        filename = f"{contract['number'].replace('/', '_')}_{report_type}.pdf"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        HTML(string=html_content).write_pdf(str(output_path))

        # 5. Update print info in contract
        await db.execute(
            update(Contract)
            .where(Contract.id == contract_id)
            .values(
                print_path=str(output_path),
                print_date=func.now(),
            )
        )

        return output_path
```

### Szablon HTML (przykład: contract.html)

```html
<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'DejaVu Sans', sans-serif; font-size: 10pt; }
    .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
    .header-left { font-size: 8pt; white-space: pre-line; }
    .title { text-align: center; font-size: 14pt; font-weight: bold; margin: 20px 0; }
    .section { margin: 10px 0; }
    .section-title { font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 3px; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    td, th { border: 1px solid #999; padding: 4px 8px; font-size: 9pt; }
    th { background: #f0f0f0; text-align: left; }
    .signatures { display: flex; justify-content: space-between; margin-top: 60px; }
    .signature-line { width: 200px; border-top: 1px solid #333; text-align: center; padding-top: 5px; }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">{{ company.header_text }}</div>
    <div class="header-right">{{ company.city }}, {{ generated_at }}</div>
  </div>

  <div class="title">
    {% if contract.contract_type == 'S' %}UMOWA NAJMU{% else %}UMOWA O ŚWIADCZENIE USŁUG{% endif %}
    nr {{ contract.number }}
  </div>

  <!-- Strony umowy -->
  <div class="section">
    <div class="section-title">Strony umowy</div>
    <p><b>Wynajmujący:</b> {{ company.name }}, NIP: {{ company.nip }}, {{ company.street }}, {{ company.postal_code }} {{ company.city }}</p>
    <p><b>Najemca:</b> {{ contract.contractor_name }}, {{ contract.delivery_address }}</p>
  </div>

  <!-- Przedmiot umowy -->
  <div class="section">
    <div class="section-title">Przedmiot umowy</div>
    <table>
      <tr><th>Lp.</th><th>Nazwa</th><th>Ilość</th><th>Stawka</th><th>Rozliczanie</th></tr>
      {% for pos in positions %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ pos.article_name or pos.description }}</td>
        <td>{{ pos.quantity }}</td>
        <td>{{ pos.unit_price }}</td>
        <td>{{ pos.billing_frequency }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <!-- Warunki -->
  <div class="section">
    <div class="section-title">Usługi dodatkowe</div>
    <p style="white-space: pre-line;">{{ contract.description }}</p>
  </div>

  {% if contract.additional_fees_text %}
  <div class="section">
    <div class="section-title">Opłaty dodatkowe</div>
    <p style="white-space: pre-line;">{{ contract.additional_fees_text }}</p>
  </div>
  {% endif %}

  <!-- Wartość -->
  <div class="section">
    <div class="section-title">Wartość umowy</div>
    <p>Wartość: {{ contract.total_value }} zł netto</p>
    {% if contract.prepayment_amount > 0 %}
    <p>Przedpłata: {{ contract.prepayment_amount }} zł ({{ contract.prepayment_document }})</p>
    {% endif %}
  </div>

  <!-- Kontakt -->
  {% if contract.show_person1 and contract.contact_person1 %}
  <div class="section">
    <p>Osoba kontaktowa: {{ contract.contact_person1 }}, tel: {{ contract.contact_phone1 }}</p>
  </div>
  {% endif %}

  <!-- Podpisy -->
  <div class="signatures">
    <div class="signature-line">Wynajmujący</div>
    <div class="signature-line">Najemca</div>
  </div>
</body>
</html>
```

---

## 4. Email (opcjonalnie, przyszłościowo)

W WinForms: context menu "Wyślij" → generuje PDF i otwiera domyślny mail client.
W nowym systemie: `POST /integrations/send-email` z załącznikiem PDF.

```python
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    attachment_path: str | None = None
```

---

## 5. Vision AI (RAO-Vision MCP) i PDF Extraction (RAO-P1-022)

### 5.1 Vision AI Server (rao-vision MCP)

**Cel:** Analiza wizualna referencyjnych PDF i screenshotów UI dla 1:1 rekonstrukcji layoutu.

**Dostępne tools:**
- `analyze_screenshot(image_path, question)` — analiza screenshotu PNG/JPG przez Claude Vision
- `screenshot_and_analyze(url, question, output_path)` — screenshot URL przez Playwright + analiza

**Użycie:**
```python
from mcp_call_tool import mcp_call_tool

result = mcp_call_tool(
    server_name="rao-vision",
    tool_name="analyze_screenshot",
    arguments={
        "image_path": "C:/projects/repos/RaoApp/backend/pdf_screenshots/ownA_p2.png",
        "question": "Opisz dokładnie pozycję pieczątki: X/Y, wymiary, format, zawartość tekstową"
    }
)
```

**Kiedy używać:**
- Tylko gdy weryfikacja programatyczna niemożliwa (layout, spacing, kolory, animacje)
- Priorytet: programatyczna (darmowa) → vision (kosztowna)
- Max 1 screenshot na zadanie

### 5.2 PDF Extraction (fitz/PyMuPDF)

**Cel:** Programowe wyciąganie obrazów (pieczątek) z referencyjnych PDF.

**Biblioteka:** fitz (PyMuPDF) — działa na Windows, Linux, macOS.

**Implementacja:**
```python
import fitz

def extract_images_from_pdf(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            # Zapisz jako plik
            with open(f"{output_dir}/page{page_num+1}_img{img_index+1}.{image_ext}", "wb") as f:
                f.write(image_bytes)
            # Zapisz jako base64
            with open(f"{output_dir}/page{page_num+1}_img{img_index+1}.{image_ext}.b64.txt", "w") as f:
                f.write(base64.b64encode(image_bytes).decode('utf-8'))
    doc.close()
```

**RAO-P1-022 - Pełna integracja pieczątek:**
- Wyekstrahowano 10 obrazów z 6 referencyjnych PDF
- Pieczątka firmowa: JPEG 12275 bytes, zawartość:
  ```
  Toolsmart Sp. z o.o.
  ul. Kłobucka 6B/103, 02-699 Warszawa
  NIP 9512598092, Regon 528847142
  KRS 0001109942
  ```
- Zapisano w `backend/reports/assets/company_stamp.jpg`
- Zintegrowano w 5 template HTML (contract.html, contract_u.html, protocol_zo.html, protocol_zo_u.html, protocol_zo_nodata_u.html)
- Użyto `file://` URI dla WeasyPrint (absolute path)
- Wymiary: 220x85px (OWN), 180x70px (protokoły)
- Weryfikacja: PDF zawiera pieczątkę na wszystkich stronach (12157 bytes vs 12275 oryginału)

**Reference PDFs:**
- `spec/archive/reference_reports/own/ownA.pdf` — OWN dla najmu
- `spec/archive/reference_reports/own/ownU.pdf` — OWN dla usług
- `spec/archive/reference_reports/S129_2026_own (1).pdf` — Umowa z OWN
- `spec/archive/reference_reports/S130_2026G_own (1).pdf` — Umowa z OWN
- `spec/archive/reference_reports/PZO_S129_2026 (1).pdf` — Protokół
- `spec/archive/reference_reports/PZO_S130_2026G (1).pdf` — Protokół

---

## 2. Fakturownia API (RAO-P2-012)

### Opis

Publiczne REST API do automatycznego pobierania kosztów z systemu fakturowania Fakturownia.

### Endpointy

```
GET /invoices.json?api_token={token}&oid={oid}
Response:
[
  {
    "id": 123,
    "number": "FV/2024/001",
    "price_net": 10000.00,
    "positions": [
      {
        "product_id": 456,
        "name": "Koparka CAT 320",
        "quantity": 1,
        "price_net": 10000.00,
        "total_price_net": 10000.00
      }
    ]
  }
]

GET /products.json?api_token={token}
Response:
[
  {
    "id": 456,
    "name": "Koparka CAT 320",
    "code": "KOP320",
    "price_net": 10000.00,
    "currency": "PLN"
  }
]
```

### Konfiguracja

**Backend:**
- `FAKTUROWNIA_ENC_KEY` w `.env` (Fernet key dla encryption tokenów)
- `backend/integrations/fakturownia/` — moduł integracji

**Frontend:**
- SettingsView → tab Fakturownia → subdomena + token
- ContractFormView → guzik 💰 (Pobierz koszty z Fakturownia)

**OID jako numer umowy (2026-05-21):**
- OID w RAO to numer umowy (contract.number)
- API Fakturownia otrzymuje OID jako numer zamówienia
- Logika pobierania używa contract.number zamiast contract.oid

### Security

- **Token encryption:** Fernet (AES-128-CBC + HMAC) at-rest w DB (api_token_ciphertext)
- **Token preview:** tylko pierwsze 4 i ostatnie 4 znaki w UI (np. "tk_****1234")
- **SSRF protection:** whitelist regex ^[a-z0-9-]+$ na subdomenie, hardcoded .fakturownia.pl
- **RBAC:** admin-only na settings/products, authenticated na invoices z ownership check
- **IDOR fix:** contract_id zamiast oid (OID pobierany z DB po weryfikacji ownership)
- **Rate limiting:** 30/min/user (invoices), 5/min/IP (settings token update)

### Mapping 1:N

Jeden produkt Fakturownia może być przypisany do wielu artykułów RAO (globalny w `articles.fakturownia_product_id`).

**Semantyka sumowania:** Jeśli artykuł z mappingiem jest na umowie → każdy dostaje pełną wartość z faktury (multiplikacja OK).

Przykład:
- Fakturownia: Koparka CAT 320 (id=456) → 10 000 zł
- RAO: Koparka 1, Koparka 2, Koparka 3 (wszystkie mają fakturownia_product_id=456)
- Umowa ma Koparka 2 i Koparka 3
- Wynik: 2x 10 000 zł = 20 000 zł (każdy pełna wartość)

### Implementacja

**Backend:**
- `backend/integrations/fakturownia/client.py` — httpx client z SSRF guard
- `backend/integrations/fakturownia/service.py` — logika 1:N mapping + sumowanie
- `backend/integrations/fakturownia/router.py` — endpointy + RBAC + rate limiting
- `backend/integrations/fakturownia/crypto.py` — Fernet encryption/decryption

**Frontend:**
- `frontend/src/stores/fakturownia.ts` — Pinia store
- `frontend/src/views/SettingsView.vue` — sekcja Fakturownia
- `frontend/src/views/ContractFormView.vue` — pole OID + guzik 💰

Implementacja z `smtplib` lub usługą zewnętrzną (SendGrid/Mailgun). Wymaga konfiguracji SMTP w `.env`.
W MVP: generowanie PDF + otwarcie `mailto:` link w przeglądarce (jak WinForms).
