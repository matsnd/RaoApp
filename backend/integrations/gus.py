import httpx
from config import settings


GUS_WSDL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
GUS_ENV = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/wsdl/WsdlRepositoryDownload/17/UslugaBIR11BIRzewnPubl.wsdl"


def _soap(action: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:a="http://www.w3.org/2005/08/addressing">
  <s:Header>
    <a:Action>{action}</a:Action>
    <a:To>{GUS_WSDL}</a:To>
  </s:Header>
  <s:Body>{body}</s:Body>
</s:Envelope>"""


class GusClient:
    async def lookup(self, nip: str) -> dict:
        from contractors.schemas import GusLookupResponse
        try:
            sid = await self._login()
            data = await self._search(sid, nip)
            await self._logout(sid)
            return GusLookupResponse(
                name=data.get("Nazwa"),
                street=data.get("Ulica"),
                building_number=data.get("NrNieruchomosci"),
                apartment_number=data.get("NrLokalu"),
                postal_code=data.get("KodPocztowy"),
                city=data.get("Miejscowosc"),
                regon=data.get("Regon"),
                province=data.get("Wojewodztwo"),
                county=data.get("Powiat"),
                community=data.get("Gmina"),
                status=data.get("StatusNip"),
            )
        except Exception as e:
            return GusLookupResponse(
                name=None, street=None, building_number=None, apartment_number=None,
                postal_code=None, city=None, regon=None, province=None,
                county=None, community=None, status=f"Błąd: {str(e)}",
            )

    async def _login(self) -> str:
        body = f"""<ns0:Zaloguj xmlns:ns0="http://CIS/BIR/PUBL/2014/07">
            <ns0:pKluczUzytkownika>{settings.RAO_GUS_API_KEY}</ns0:pKluczUzytkownika>
        </ns0:Zaloguj>"""
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GUS_WSDL, content=_soap("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj", body), headers=headers)
            import re
            match = re.search(r"<ZalogujResult>(.*?)</ZalogujResult>", resp.text)
            return match.group(1) if match else ""

    async def _search(self, sid: str, nip: str) -> dict:
        import xml.etree.ElementTree as ET
        body = f"""<ns0:DaneSzukajPodmioty xmlns:ns0="http://CIS/BIR/PUBL/2014/07">
            <ns0:pParametryWyszukiwania>
                <ns1:Nip xmlns:ns1="http://CIS/BIR/2014/07">{nip}</ns1:Nip>
            </ns0:pParametryWyszukiwania>
        </ns0:DaneSzukajPodmioty>"""
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty",
            "sid": sid,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GUS_WSDL, content=_soap("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty", body), headers=headers)
            import re
            match = re.search(r"<DaneSzukajPodmiotyResult>(.*?)</DaneSzukajPodmiotyResult>", resp.text, re.DOTALL)
            if not match:
                return {}
            inner_xml = match.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            try:
                root = ET.fromstring(inner_xml)
                result = {}
                for child in root.iter():
                    result[child.tag] = child.text
                return result
            except Exception:
                return {}

    async def _logout(self, sid: str):
        body = f"""<ns0:Wyloguj xmlns:ns0="http://CIS/BIR/PUBL/2014/07">
            <ns0:pIdentyfikatorSesji>{sid}</ns0:pIdentyfikatorSesji>
        </ns0:Wyloguj>"""
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj",
            "sid": sid,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(GUS_WSDL, content=_soap("http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj", body), headers=headers)


gus_client = GusClient()
