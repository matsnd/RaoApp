from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    login: str
    email: str | None
    first_name: str | None
    last_name: str | None
    role: str
    branch_id: int | None
    is_active: bool
    last_login: datetime | None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    must_change_password: bool = False


class RegisterRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str | None = None
    last_name: str | None = None
    role: Literal["admin", "user", "viewer"] = "user"
    branch_id: int | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=100)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class ProfileUpdate(BaseModel):
    email: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=30)
    last_name: str | None = Field(None, max_length=30)


class UserListItem(BaseModel):
    id: int
    login: str
    email: str | None
    first_name: str | None
    last_name: str | None
    role: str
    branch_id: int | None
    branch_name: str | None
    is_active: bool
    last_login: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=30)
    last_name: str | None = Field(None, max_length=30)
    role: Literal["admin", "user", "viewer"] | None = None
    branch_id: int | None = None
    is_active: bool | None = None
