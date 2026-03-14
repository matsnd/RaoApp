from decimal import Decimal
import httpx
from config import settings


class NominatimClient:
    async def reverse_geocode(self, lat: Decimal, lng: Decimal) -> dict:
        url = f"{settings.RAO_NOMINATIM_BASE_URL}/reverse"
        params = {"lat": str(lat), "lon": str(lng), "format": "json", "addressdetails": "1"}
        headers = {"User-Agent": "RAO-App/1.0", "Accept-Language": "pl"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("address", {})


nominatim_client = NominatimClient()
