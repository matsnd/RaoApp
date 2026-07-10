from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional


class ReservationCreate(BaseModel):
    article_id: int
    reserved_from: date
    reserved_to: date
    note: Optional[str] = Field(None, max_length=300)

    @model_validator(mode="after")
    def validate_dates(self) -> "ReservationCreate":
        if self.reserved_from > self.reserved_to:
            raise ValueError("reserved_from must be <= reserved_to")
        return self


class ReservationUpdate(BaseModel):
    reserved_from: Optional[date] = None
    reserved_to: Optional[date] = None
    note: Optional[str] = Field(None, max_length=300)


class ReservationResponse(BaseModel):
    id: int
    article_id: int
    reserved_from: date
    reserved_to: date
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ReservationWithArticleResponse(BaseModel):
    id: int
    article_id: int
    article_name: Optional[str] = None
    internal_number: Optional[str] = None
    reserved_from: date
    reserved_to: date
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
