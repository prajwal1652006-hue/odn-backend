from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.models.user import UserRole
from app.models.rider import VehicleType

class UserRegisterRequest(BaseModel):
    phone_number: str = Field(..., example="+919876543210")
    password: str = Field(..., min_length=6, example="SecurePass123!")
    full_name: str = Field(..., example="Ramesh Kumar")
    role: UserRole

    # Fields required if role == RIDER
    vehicle_type: Optional[VehicleType] = Field(default=VehicleType.BIKE)
    license_number: Optional[str] = Field(default=None, example="KA-01-2024-00123")

    # Fields required if role == BUSINESS
    business_name: Optional[str] = Field(default=None, example="Fresh Mart Kirana")
    business_category: Optional[str] = Field(default=None, example="GROCERY")
    pickup_address: Optional[str] = Field(default=None, example="100 Feet Rd, Indiranagar, Bengaluru")
    pickup_latitude: Optional[float] = Field(default=None, example=12.9783)
    pickup_longitude: Optional[float] = Field(default=None, example=77.6408)

class UserLoginRequest(BaseModel):
    phone_number: str = Field(..., example="+919876543210")
    password: str = Field(..., example="SecurePass123!")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    role: UserRole
    full_name: str

class UserProfileResponse(BaseModel):
    id: UUID
    phone_number: str
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

class GoogleLoginRequest(BaseModel):
    id_token: str = Field(default="google_id_token_demo")
    role: str = Field(default="RIDER")
