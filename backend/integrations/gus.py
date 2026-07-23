import sys
import httpx
from config import settings
from lxml import etree

# Production servers (cPanel/LiteSpeed) use ASCII stdout — polskie znaki w
# danych GUS (ń, ó, ł) powodują UnicodeEncodeError w print(). Rekonfiguracja
# stdout na UTF-8 z errors='replace' naprawia to bez zmieniania printów.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Production URL (from old app)
# Note: Test endpoint (wyszukiwarkaregontest) has no real data - only for integration testing
# This production endpoint works with production API key from GUS
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
        
        Integration status: WORKING (authentication OK, but limited data access)
        - API key authentication: ✅ (login returns session ID)
        - Search method: DaneSzukajPodmioty (official BIR11 API method)
        - Endpoint: Production GUS API (wyszukiwarkaregon.stat.gov.pl)
        
        Note: All tested NIPs return ErrorCode 4 ("Nie znaleziono wpisu dla podanych kryteriów wyszukiwania")
        This may indicate that the API key has limited access to the GUS database.
        For production use, ensure the API key has proper permissions from GUS.
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
        print(f"[GUS] Login status: {resp.status_code}")
        print(f"[GUS] Login response length: {len(resp.text)}")

        # Handle MTOM/XOP response - extract XML from multipart
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)
            print(f"[GUS] Extracted XML length: {len(content)}")

        tree = etree.fromstring(content.encode())
        sid = tree.find(".//{http://CIS/BIR/PUBL/2014/07}ZalogujResult")
        sid_text = sid.text if sid is not None else ""
        print(f"[GUS] Session ID: {sid_text}")
        return sid_text

    async def _search(self, client: httpx.AsyncClient, nip: str) -> dict:
        # Use DaneSzukajPodmioty method (official BIR11 API method)
        print(f"[GUS] Searching for NIP: {nip}")
        
        body = (
            f'<ns:DaneSzukajPodmioty xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            f'<ns:pParametryWyszukiwania>'
            f'<dat:Nip xmlns:dat="http://CIS/BIR/PUBL/2014/07/DataContract">{nip}</dat:Nip>'
            f'</ns:pParametryWyszukiwania>'
            f'</ns:DaneSzukajPodmioty>'
        )
        headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
        if self.sid:
            headers["sid"] = self.sid

        resp = await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty", body),
            headers=headers)
        print(f"[GUS] Search status: {resp.status_code}")
        print(f"[GUS] Search response length: {len(resp.text)}")

        # Handle MTOM/XOP response - extract XML from multipart
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)
            print(f"[GUS] Extracted XML length: {len(content)}")

        # Parse response — XML embedded in CDATA
        tree = etree.fromstring(content.encode())
        result_el = tree.find(".//{http://CIS/BIR/PUBL/2014/07}DaneSzukajPodmiotyResult")
        if result_el is None:
            print(f"[GUS] No result element found")
            return {}
        if not result_el.text:
            print(f"[GUS] Result element found but empty - trying full report")
            # Try full report instead
            return await self._get_full_report(client, nip)
        inner = etree.fromstring(result_el.text.encode())
        dane = inner.find(".//dane")
        if dane is None:
            print(f"[GUS] No dane element found")
            return {}
        result = {child.tag: child.text for child in dane}
        print(f"[GUS] Parsed data: {result}")
        return result

    async def _get_full_report(self, client: httpx.AsyncClient, nip: str) -> dict:
        print(f"[GUS] Trying full report for NIP: {nip}")
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
        print(f"[GUS] Full report status: {resp.status_code}")
        print(f"[GUS] Full report response length: {len(resp.text)}")

        # Save full response for debugging
        with open('gus_full_report_response.txt', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        print("[GUS] Full report response saved to gus_full_report_response.txt")

        # Handle MTOM/XOP response
        content = resp.text
        import re
        xml_match = re.search(r'<s:Envelope[^>]*>.*?</s:Envelope>', content, re.DOTALL)
        if xml_match:
            content = xml_match.group(0)
            print(f"[GUS] Extracted full report XML length: {len(content)}")

        # Parse response
        tree = etree.fromstring(content.encode())
        result_el = tree.find(".//{http://CIS/BIR/PUBL/2014/07}DanePobierzPelnyRaportResult")
        if result_el is None or not result_el.text:
            print(f"[GUS] No full report result")
            return {}
        
        print(f"[GUS] Full report data length: {len(result_el.text)}")
        print(f"[GUS] Full report data preview: {result_el.text[:200]}")
        
        # Parse full report XML
        try:
            inner = etree.fromstring(result_el.text.encode())
            dane = inner.find(".//dane")
            if dane is None:
                print(f"[GUS] No dane in full report, trying to find any data")
                # Try to find any data element
                all_elements = inner.xpath(".//*")
                print(f"[GUS] Found {len(all_elements)} elements in full report")
                for elem in all_elements[:10]:  # First 10 elements
                    print(f"[GUS] Element: {elem.tag} = {elem.text[:50] if elem.text else 'None'}")
                return {}
            result = {child.tag: child.text for child in dane}
            print(f"[GUS] Parsed full report data: {result}")
            return result
        except Exception as e:
            print(f"[GUS] Error parsing full report: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def _logout(self, client: httpx.AsyncClient):
        body = f'<ns:Wyloguj xmlns:ns="http://CIS/BIR/PUBL/2014/07"><ns:pIdentyfikatorSesji>{self.sid}</ns:pIdentyfikatorSesji></ns:Wyloguj>'
        await client.post(GUS_WSDL, content=_build_envelope("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj", body),
            headers={"Content-Type": "application/soap+xml; charset=utf-8"})


gus_client = GusClient()
