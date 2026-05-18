from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth.dependencies import get_current_user
from auth.models import User
from database import AsyncSessionLocal

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


class GeocodeRequest(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    lat: Decimal | None = None
    lon: Decimal | None = None
    address: dict | None = None


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
    """Forward geocoding: address -> lat/lng (RAO-P2-005)"""
    from integrations.nominatim import nominatim_client
    result = await nominatim_client.geocode(data.address)
    return GeocodeResponse(
        lat=result.get("lat"),
        lon=result.get("lon"),
        address=result.get("address"),
    )


@router.get("/postal-codes/{code}", response_model=PostalCodeLookupResponse)
async def lookup_postal_code(
    code: str,
    _: User = Depends(get_current_user),
):
    """Lookup city by postal code from dictionary (RAO-P1-008)."""
    import re
    if not re.match(r"^\d{2}-\d{3}$", code):
        raise HTTPException(status_code=422, detail="Invalid postal code format. Expected XX-XXX")
    
    async with AsyncSessionLocal() as db:
        from integrations.models import PostalCode
        result = await db.execute(
            select(PostalCode).where(PostalCode.code == code).limit(1)
        )
        postal = result.scalar_one_or_none()
        if not postal:
            raise HTTPException(status_code=404, detail="Postal code not found in dictionary")
        return PostalCodeLookupResponse(
            code=postal.code,
            city=postal.city,
            voivodeship=postal.voivodeship,
        )
