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

Produkcyjny WSDL: `https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnworki.svc`
Testowy WSDL: `https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnworki.svc`

### Kroki SOAP

```python
# 1. ZALOGUJ — uzyskaj session ID
# SOAPAction: http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Zaloguj
# Body:
"""
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:ns="http://CIS/BIR/PUBL/2014/07">
  <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
    <wsa:To>https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnworki.svc</wsa:To>
    <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Zaloguj</wsa:Action>
  </soap:Header>
  <soap:Body>
    <ns:Zaloguj>
      <ns:pKluczUzytkownika>{api_key}</ns:pKluczUzytkownika>
    </ns:Zaloguj>
  </soap:Body>
</soap:Envelope>
"""
# Response: <ZalogujResult>{session_id}</ZalogujResult>

# 2. SZUKAJ PO NIP
# SOAPAction: http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/DaneSzukajPodmioty
# Header: sid={session_id}
# Body:
"""
<ns:DaneSzukajPodmioty>
  <ns:pParametryWyszukiwania>
    <dat:Nip xmlns:dat="http://CIS/BIR/2014/07/DataContract">{nip}</dat:Nip>
  </ns:pParametryWyszukiwania>
</ns:DaneSzukajPodmioty>
"""
# Response XML zawiera: Regon, Nazwa, Miejscowosc, KodPocztowy, Ulica itp.

# 3. POBIERZ PEŁNY RAPORT (opcjonalnie, dla więcej danych)
# SOAPAction: http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/DanePobierzPelnyRaport
# Raporty:
#   - Osoby prawne: "BIR11OsPrawna"
#   - JDG: "BIR11OsFizycznaDzworkalnosci"

# 4. WYLOGUJ
# SOAPAction: http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Wyloguj
```

### Implementacja w Python

```python
# integrations/gus.py
import httpx
from lxml import etree

class GusClient:
    WSDL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnworki.svc"
    NS = {"soap": "http://www.w3.org/2003/05/soap-envelope"}

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.sid: str | None = None

    async def lookup_by_nip(self, nip: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.sid = await self._login(client)
            try:
                result = await self._search(client, nip)
                return result
            finally:
                await self._logout(client)

    async def _login(self, client: httpx.AsyncClient) -> str:
        body = self._build_envelope(
            "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Zaloguj",
            f'<ns:Zaloguj xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pKluczUzytkownika>{self.api_key}</ns:pKluczUzytkownika>'
            f'</ns:Zaloguj>'
        )
        resp = await client.post(self.WSDL, content=body,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        tree = etree.fromstring(resp.content)
        sid = tree.find(".//{http://CIS/BIR/PUBL/2014/07}ZalogujResult")
        return sid.text if sid is not None else ""

    async def _search(self, client: httpx.AsyncClient, nip: str) -> dict:
        body = self._build_envelope(
            "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/DaneSzukajPodmioty",
            f'<ns:DaneSzukajPodmioty xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pParametryWyszukiwania>'
            f'<dat:Nip xmlns:dat="http://CIS/BIR/2014/07/DataContract">{nip}</dat:Nip>'
            f'</ns:pParametryWyszukiwania>'
            f'</ns:DaneSzukajPodmioty>'
        )
        resp = await client.post(self.WSDL, content=body,
            headers={"Content-Type": "application/soap+xml; charset=utf-8", "sid": self.sid})
        # Parse response — XML embedded in CDATA
        tree = etree.fromstring(resp.content)
        result_el = tree.find(".//{http://CIS/BIR/PUBL/2014/07}DaneSzukajPodmiotyResult")
        if result_el is None or not result_el.text:
            return {}
        inner = etree.fromstring(result_el.text.encode())
        dane = inner.find(".//dane")
        if dane is None:
            return {}
        return {child.tag: child.text for child in dane}

    async def _logout(self, client: httpx.AsyncClient):
        body = self._build_envelope(
            "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzworki/Wyloguj",
            f'<ns:Wyloguj xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pIdentyfikatorSesji>{self.sid}</ns:pIdentyfikatorSesji>'
            f'</ns:Wyloguj>'
        )
        await client.post(self.WSDL, content=body,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"})

    def _build_envelope(self, action: str, body_content: str) -> str:
        return (
            f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
            f'<soap:Header><wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">{self.WSDL}</wsa:To>'
            f'<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">{action}</wsa:Action>'
            f'</soap:Header>'
            f'<soap:Body>{body_content}</soap:Body>'
            f'</soap:Envelope>'
        )
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

Implementacja z `smtplib` lub usługą zewnętrzną (SendGrid/Mailgun). Wymaga konfiguracji SMTP w `.env`.
W MVP: generowanie PDF + otwarcie `mailto:` link w przeglądarce (jak WinForms).
