import uuid
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str = Field(min_length=8)
    birth_date: date | None = None

    @field_validator("birth_date", mode="before")
    @classmethod
    def parse_birth_date(cls, value: object) -> date | None:
        if not value:
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return date.fromisoformat(value)
            except Exception:
                return None
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordLogin(BaseModel):
    email: EmailStr
    birth_date: date
    new_password: str | None = Field(default=None, min_length=8)

    @field_validator("birth_date", mode="before")
    @classmethod
    def parse_recovery_birth_date(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            try:
                return date.fromisoformat(value)
            except Exception:
                return value
        return value


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None = None
    birth_date: date | None = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str | None = None
