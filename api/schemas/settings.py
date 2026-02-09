from pydantic import BaseModel
from typing import Optional

class SettingSchema(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    settings: dict[str, str]
