from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.order import OrderStatus, OrderPriority

class CreateOrderRequest(BaseModel):
    priority: OrderPriority = Field(default=OrderPriority.STANDARD)
    pickup_address: str = Field(..., example="Store 12, Indiranagar 100ft Rd, Bengaluru")
    pickup_latitude: float = Field(..., example=12.9783)
    pickup_longitude: float = Field(..., example=77.6408)
    dropoff_address: str = Field(..., example="Flat 402, Sunshine Apts, Domlur, Bengaluru")
    dropoff_latitude: float = Field(..., example=12.9609)
    dropoff_longitude: float = Field(..., example=77.6387)
    customer_name: str = Field(..., example="Anita Roy")
    customer_phone: str = Field(..., example="+919123456789")

class OrderResponse(BaseModel):
    id: UUID
    business_id: UUID
    rider_id: Optional[UUID] = None
    status: OrderStatus
    priority: OrderPriority
    pickup_address: str
    dropoff_address: str
    customer_name: str
    customer_phone: str
    delivery_fee: float
    otp_code: str
    created_at: datetime

    class Config:
        from_attributes = True

class NearbyOrderResponse(BaseModel):
    order_id: UUID
    business_name: str
    priority: OrderPriority
    pickup_address: str
    dropoff_address: str
    distance_to_pickup_km: float
    trip_distance_km: float
    delivery_fee: float
    created_at: datetime