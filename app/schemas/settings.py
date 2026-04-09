from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserSettingsBase(BaseModel):
    language: str = Field(default="uz", min_length=2, max_length=16)
    is_language_manually_selected: bool = False
    theme: str = Field(default="system", min_length=3, max_length=32)
    halal_mode_enabled: bool = False
    healthy_mode_enabled: bool = False
    vegan_mode_enabled: bool = False
    notifications_enabled: bool = True
    selected_allergens: list[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    onboarding_shown: bool = False


class UserSettingsRead(UserSettingsBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(UserSettingsBase):
    pass
