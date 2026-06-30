from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth.dependencies import get_current_user
from auth.models import User
from database import AsyncSessionLocal
from contractors.schemas import GusLookupRequest, GusLookupResponse

PostalCodeType = Annotated[str, "Postal code in format XX-XXX"]

router = APIRouter(prefix="/integrations", tags=["integrations"])


class ReverseGeocodeRequest(BaseModel):
    latitude: Decimal
    longitude: Decimal


class ReverseGeocodeResponse(BaseModel):
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    hamlet: str | None = None
    city: str | None = None
    town: str | None = None
    village: str | None = None
    county: str | None = None
    municipality: str | None = None
    province: str | None = None
    district: str | None = None
    neighbourhood: str | None = None


class PostalCodeLookupResponse(BaseModel):
    code: str
    city: str
    voivodeship: str | None = None
    powiat: str | None = None      # RAO-P2-028: pełna hierarchia terytorialna
    gmina: str | None = None       # RAO-P2-028: pełna hierarchia terytorialna


class GeocodeRequest(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    lat: Decimal | None = None
    lon: Decimal | None = None
    address: dict | None = None
    city: str | None = None
    postal_code: str | None = None


@router.post("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(
    data: ReverseGeocodeRequest,
    _: User = Depends(get_current_user),
):
    from integrations.nominatim import nominatim_client
    addr = await nominatim_client.reverse_geocode(data.latitude, data.longitude)
    return ReverseGeocodeResponse(
        street=addr.get("road"),
        house_number=addr.get("house_number"),
        postal_code=addr.get("postcode"),
        hamlet=addr.get("hamlet"),
        city=addr.get("city"),
        town=addr.get("town"),
        village=addr.get("village"),
        county=addr.get("county"),
        municipality=addr.get("municipality"),
        province=addr.get("state"),
        district=addr.get("district"),
        neighbourhood=addr.get("neighbourhood"),
    )


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode(
    data: GeocodeRequest,
    _: User = Depends(get_current_user),
):
    """Forward geocoding: address -> lat/lng + city + postal_code (RAO-P2-005, P1-017)"""
    from integrations.nominatim import nominatim_client
    result = await nominatim_client.geocode(data.address)
    return GeocodeResponse(
        lat=result.get("lat"),
        lon=result.get("lon"),
        address=result.get("address"),
        city=result.get("city"),
        postal_code=result.get("postal_code"),
    )


class ExtractAddressRequest(BaseModel):
    address: str


class ExtractAddressResponse(BaseModel):
    """Hybrid address extraction result (P1-017).

    city/postal_code filled by offline regex first, Nominatim fallback.
    self_pickup=True when 'odbiór własny' detected — skip Nominatim.
    """
    city: str | None = None
    postal_code: str | None = None
    lat: Decimal | None = None
    lon: Decimal | None = None
    self_pickup: bool = False
    source: str = "none"  # "self_pickup" | "offline" | "nominatim" | "none"


@router.post("/extract-address", response_model=ExtractAddressResponse)
async def extract_address(
    data: ExtractAddressRequest,
    _: User = Depends(get_current_user),
):
    """Hybrid address extraction from free-text delivery_address (P1-017).

    Algorithm (per PO recommendation):
    1. Clean: remove \\r\\n, collapse whitespace
    2. Early-exit: 'odbiór własny' → self_pickup=True, no city/postal
    3. Offline postal_code regex \\d{2}-\\d{3}
    4. Offline city match via explorer.extract_city() (40+ Polish cities)
    5. Nominatim fallback (only if step 4 returned 'Nieznane')
    """
    from integrations.nominatim import (
        nominatim_client, clean_address, is_self_pickup,
        extract_postal_code, extract_city_from_nominatim,
    )
    from explorer.router import extract_city as extract_city_offline

    cleaned = clean_address(data.address)
    if not cleaned:
        return ExtractAddressResponse()

    # Step 2: self-pickup early exit
    if is_self_pickup(cleaned):
        return ExtractAddressResponse(self_pickup=True, source="self_pickup")

    # Step 3: offline postal code
    postal = extract_postal_code(cleaned)

    # Step 4: offline city
    city_offline = extract_city_offline(cleaned)
    city = None if city_offline == "Nieznane" else city_offline

    # If we have both from offline — done, no Nominatim call
    if city and postal:
        return ExtractAddressResponse(
            city=city, postal_code=postal, source="offline",
        )

    # Step 5: Nominatim fallback (only if offline city not found)
    if not city:
        try:
            result = await nominatim_client.geocode(cleaned)
            if result:
                nom_city = result.get("city")
                nom_postal = result.get("postal_code")
                return ExtractAddressResponse(
                    city=nom_city or city,
                    postal_code=postal or nom_postal,
                    lat=result.get("lat"),
                    lon=result.get("lon"),
                    source="nominatim",
                )
        except Exception:
            pass  # silent fail — Nominatim may be down or rate-limited

    # Fallback: return what we have from offline
    return ExtractAddressResponse(
        city=city, postal_code=postal,
        source="offline" if (city or postal) else "none",
    )


@router.get("/postal-codes/{code}", response_model=PostalCodeLookupResponse)
async def lookup_postal_code(
    code: str,
    _: User = Depends(get_current_user),
):
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
            powiat=postal.powiat,
            gmina=postal.gmina,
        )


class TerytSyncResponse(BaseModel):
    success: bool
    message: str
    count: int


@router.post("/gus-lookup")
async def gus_lookup(
    data: GusLookupRequest,
    _: User = Depends(get_current_user),
):
    """Lookup company data from GUS REGON API by NIP (RAO-P1-030)."""
    from integrations.gus import gus_client
    result = await gus_client.lookup(data.nip)
    # Return as dict to avoid Pydantic serialization issues
    return {
        "name": result.name,
        "street": result.street,
        "building_number": result.building_number,
        "apartment_number": result.apartment_number,
        "postal_code": result.postal_code,
        "city": result.city,
        "regon": result.regon,
        "province": result.province,
        "county": result.county,
        "community": result.community,
        "status": result.status,
    }


@router.post("/teryt/sync", response_model=TerytSyncResponse)
async def sync_teryt_data(
    _: User = Depends(get_current_user),
):
    """
    Sync postal codes from pre-generated SQL inserts (RAO-P2-015).
    Loads data from backend/integrations/teryt/postal_codes_inserts.sql
    """
    import os
    import sqlalchemy as sa

    # Wczytaj SQL inserty
    sql_file = os.path.join(
        os.path.dirname(__file__),
        "teryt",
        "postal_codes_inserts.sql"
    )

    if not os.path.exists(sql_file):
        raise HTTPException(
            status_code=404,
            detail="SQL file not found. Run fetch_postal_codes.py first."
        )

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    async with AsyncSessionLocal() as db:
        try:
            # Usuń stare dane
            await db.execute(sa.text("DELETE FROM postal_codes"))
            # Wczytaj nowe dane
            await db.execute(sa.text(sql_content))
            await db.commit()

            # Policz rekordy
            result = await db.execute(sa.text("SELECT COUNT(*) FROM postal_codes"))
            count = result.scalar()

            return TerytSyncResponse(
                success=True,
                message=f"Successfully synced {count} postal codes",
                count=count
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync postal codes: {str(e)}"
            )
