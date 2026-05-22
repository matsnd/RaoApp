from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class AddressResponse(BaseModel):
    id: int
    contractor_id: int
    name: str | None
    country_code: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    notes: str | None
    contact_person: str | None
    phone: str | None
    email: str | None
    is_default_delivery: bool
    is_headquarters: bool
    latitude: Decimal | None
    longitude: Decimal | None

    class Config:
        from_attributes = True


class AddressCreate(BaseModel):
    name: str | None = Field(None, max_length=200)
    country_code: str = Field("PL", max_length=3)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=50)
    street: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=200)
    contact_person: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=20)
    is_default_delivery: bool = False
    is_headquarters: bool = False
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class ContractorListItem(BaseModel):
    id: int
    name: str
    name_short: str | None
    nip: str | None
    city: str | None
    street: str | None
    is_supplier: bool
    phone1: str | None
    email: str | None
    active_contract_number: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ContractorDetail(BaseModel):
    id: int
    name: str
    name_short: str | None
    nip: str | None
    regon: str | None
    pesel: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    unit: str | None
    notes: str | None
    is_supplier: bool
    email: str | None
    contact_person1: str | None
    phone1: str | None
    contact_person2: str | None
    phone2: str | None
    landline_phone: str | None
    website: str | None
    files_folder: str | None
    gus_date: datetime | None
    created_at: datetime
    updated_at: datetime | None
    addresses: list[AddressResponse] = []

    class Config:
        from_attributes = True


class ContractorCreate(BaseModel):
    name: str = Field(..., max_length=400)
    name_short: str | None = Field(None, max_length=200)
    nip: str | None = Field(None, max_length=20)
    regon: str | None = Field(None, max_length=20)
    pesel: str | None = Field(None, max_length=20)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=50)
    street: str | None = Field(None, max_length=50)
    unit: str | None = Field(None, max_length=50)
    notes: str | None = None
    is_supplier: bool = False
    email: str | None = Field(None, max_length=100)
    contact_person1: str | None = Field(None, max_length=100)
    phone1: str | None = Field(None, max_length=100)
    contact_person2: str | None = Field(None, max_length=100)
    phone2: str | None = Field(None, max_length=100)
    landline_phone: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=100)

    @field_validator('nip')
    @classmethod
    def validate_nip(cls, v: str | None) -> str | None:
        if v is None or v.strip() == '':
            return None
        from contractors.service import validate_nip_checksum
        if not validate_nip_checksum(v):
            raise ValueError('Nieprawidłowy numer NIP - błędna suma kontrolna')
        return v


class GusLookupRequest(BaseModel):
    nip: str = Field(..., pattern=r"^\d{10}$")


class GusLookupResponse(BaseModel):
    name: str | None
    street: str | None
    building_number: str | None
    apartment_number: str | None
    postal_code: str | None
    city: str | None
    regon: str | None
    province: str | None
    county: str | None
    community: str | None
    status: str | None
