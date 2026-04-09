from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
