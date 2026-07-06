from decimal import Decimal
import re
import httpx
from config import settings


# Self-pickup phrases — skip Nominatim entirely (P1-017, PO recommendation)
SELF_PICKUP_PATTERNS = [
    "odbiór własny", "odbiór osobisty", "własny odbiór", "klient odbiera",
    "odbiór we własnym zakresie", "odbiorca odbiera", "odbiór w siedzibie",
]


def is_self_pickup(address: str) -> bool:
    """Check if delivery_address indicates self-pickup (no delivery)."""
    if not address:
        return False
    addr_lower = address.lower()
    return any(p in addr_lower for p in SELF_PICKUP_PATTERNS)


def clean_address(address: str) -> str:
    """Clean delivery_address: remove \\r\\n, collapse whitespace, trim."""
    if not address:
        return ""
    cleaned = address.replace("\r", " ").replace("\n", " ")
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_postal_code(address: str) -> str | None:
    """Extract Polish postal code (XX-XXX) from free-text address.

    Handles:
    - '01-320 Warszawa' → '01-320'
    - '27-220Mirzec' (no space) → '27-220'
    - '05-506 Kolonia Lesznowola' → '05-506'
    """
    if not address:
        return None
    m = re.search(r'(\d{2}-\d{3})', address)
    return m.group(1) if m else None


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


def extract_city_from_nominatim(address: dict) -> str | None:
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
                lat_raw = result.get("lat")
                lon_raw = result.get("lon")
                return {
                    "lat": Decimal(lat_raw) if lat_raw is not None else None,
                    "lon": Decimal(lon_raw) if lon_raw is not None else None,
                    "address": addr,
                    "city": extract_city_from_nominatim(addr),
                    "postal_code": addr.get("postcode"),
                }
            return {}


nominatim_client = NominatimClient()
