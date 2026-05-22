import httpx
from config import settings


class GusClient:
    def __init__(self):
        self.api_key = settings.RAO_GUS_API_KEY

    async def lookup(self, nip: str) -> dict:
        from contractors.schemas import GusLookupResponse
        try:
            # Klucz GUS ze starej aplikacji (d4feaf84608747c1addd) nie działa - zwraca pusty <ZalogujResult/>
            # Oznacza to, że klucz jest nieprawidłowy lub wygasły
            # Zwracamy mock data z informacją o problemie
            return GusLookupResponse(
                name="Firma Testowa Sp. z o.o.",
                street="ul. Testowa 1",
                building_number="1",
                apartment_number="2",
                postal_code="00-000",
                city="Warszawa",
                regon="123456789",
                province="mazowieckie",
                county="Warszawa",
                community="Warszawa",
                status="Aktywny (mock data - klucz GUS ze starej aplikacji nie działa, potrzebny nowy klucz z https://api.stat.gov.pl/Home/RegonApi)",
            )
        except Exception as e:
            return GusLookupResponse(
                name=None, street=None, building_number=None, apartment_number=None,
                postal_code=None, city=None, regon=None, province=None,
                county=None, community=None, status=f"Błąd: {str(e)}",
            )


gus_client = GusClient()
