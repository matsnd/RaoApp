from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import get_current_user
from auth.models import User

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
