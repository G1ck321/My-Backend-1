import re

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FrontendPayRequest(BaseModel):
    """Validate the checkout payload sent from the frontend before processing."""

    # Customer identity and delivery details.
    name: str = Field(..., min_length=1)
    phone: str
    matricNumber: Optional[str] = None
    address: str
    email: str
    roomNumber: str
    orderDetails: str
    amount: float = Field(..., gt=0)

    @field_validator("matricNumber", mode="before")
    @classmethod
    def validate_matric_number(cls, value):
        # Keep the field optional, but normalize it when the user does send one.
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise ValueError("matricNumber must be a string")

        normalized_value = value.strip().upper()
        if not re.fullmatch(r"\d{2}[A-Z]{2}\d{6}", normalized_value):
            raise ValueError("matricNumber must match the format 12AB345678")

        return normalized_value