from decimal import Decimal
import re
import httpx
from config import settings


def normalize_address(address: str) -> str:
    """Normalize address for Nominatim geocoding (P1-017).

    Nominatim returns EMPTY for 'ul. Kłobucka 6B, 02-699 Warszawa'
    but works for 'Kłobucka 6B, 02-699 Warszawa'. The 'ul.' prefix
    and other Polish street prefixes break the search.
    """
    if not address:
        return ""
    # Remove Polish street prefixes: ul., al., pl., os., osiedle
    cleaned = re.sub(r'^\s*(ul\.|ulica|al\.|aleja|pl\.|plac|os\.|osiedle)\s+', '', address, flags=re.IGNORECASE)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_city(address: dict) -> str | None:
    """Extract city from Nominatim address dict.

    Nominatim returns city in different fields depending on location:
    city (large cities), town (medium), village (small), hamlet (tiny).
    """
    return (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("hamlet")
        or address.get("municipality")
    )


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

    async def geocode(self, address: str) -> dict:
        """Forward geocoding: address -> lat/lng + city + postal_code (P1-017)"""
        normalized = normalize_address(address)
        if not normalized:
            return {}
        url = f"{settings.RAO_NOMINATIM_BASE_URL}/search"
        params = {"q": normalized, "format": "json", "limit": 1, "addressdetails": 1}
        headers = {"User-Agent": "RAO-App/1.0", "Accept-Language": "pl"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if data:
                result = data[0]
                addr = result.get("address", {})
                return {
                    "lat": Decimal(result.get("lat")),
                    "lon": Decimal(result.get("lon")),
                    "address": addr,
                    "city": extract_city(addr),
                    "postal_code": addr.get("postcode"),
                }
            return {}


nominatim_client = NominatimClient()
