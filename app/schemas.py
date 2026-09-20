from typing import Any

from pydantic import BaseModel


class ReverseGeocodeResponse(BaseModel):
    name: str
    properties: dict[str, Any]
    matched_exact: bool


class UploadResult(BaseModel):
    filename: str
    name_field: str
    feature_count: int
    fields_available: list[str]
