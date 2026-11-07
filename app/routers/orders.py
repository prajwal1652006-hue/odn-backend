import random
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.elements import WKTElement

from app.database import get_db
from app.models.user import User, UserRole
from app.models.business import Business
from app.models.rider import Rider
from app.models.order import Order, OrderStatus
from app.schemas.order import CreateOrderRequest, OrderResponse, NearbyOrderResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/orders", tags=["Orders & Logistics"])

def calculate_fee_and_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    """Calculates approximate distance in km using Haversine formula and computes fee in INR."""
    import math
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = round(R * c, 2)
    
    # Base fee structure: ₹35 base + ₹12 per km
    fee = round(35.00 + (distance_km * 12.00), 2)
    return distance_km, max(fee, 40.00)

@router.post("/create", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.BUSINESS:
        raise HTTPException(status_code=403, detail="Only registered business accounts can create delivery requests")

    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")

    pickup_geom = WKTElement(f"POINT({payload.pickup_longitude} {payload.pickup_latitude})", srid=4326)
    dropoff_geom = WKTElement(f"POINT({payload.dropoff_longitude} {payload.dropoff_latitude})", srid=4326)

    dist_km, delivery_fee = calculate_fee_and_distance(
        payload.pickup_latitude, payload.pickup_longitude,
        payload.dropoff_latitude, payload.dropoff_longitude
    )

    otp_code = f"{random.randint(100000, 999999)}"

    new_order = Order(
        business_id=business.id,
        status=OrderStatus.CREATED,
        priority=payload.priority,
        pickup_location=pickup_geom,
        pickup_address=payload.pickup_address,
        dropoff_location=dropoff_geom,
        dropoff_address=payload.dropoff_address,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        delivery_fee=delivery_fee,
        otp_code=otp_code
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/available", response_model=List[NearbyOrderResponse])
def get_available_nearby_orders(
    latitude: float = Query(..., example=12.9781),
    longitude: float = Query(..., example=77.6402),
    radius_km: float = Query(default=5.0, example=5.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.RIDER:
        raise HTTPException(status_code=403, detail="Only delivery partners can view nearby requests")

    rider_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
    radius_meters = radius_km * 1000.0

    # Query unassigned orders within radius using PostGIS spatial functions
    query_results = (
        db.query(
            Order,
            Business.business_name,
            func.ST_Distance(Order.pickup_location, rider_point).label("dist_meters")
        )
        .join(Business, Order.business_id == Business.id)
        .filter(Order.status == OrderStatus.CREATED)
        .filter(Order.rider_id == None)
        .filter(func.ST_DWithin(Order.pickup_location, rider_point, radius_meters))
        .order_by("dist_meters")
        .limit(20)
        .all()
    )

    available_orders = []
    for order, b_name, dist_meters in query_results:
        pickup_km = round(dist_meters / 1000.0, 2)
        # Dummy calculation for trip distance for listing card view
        trip_km = round(pickup_km + 2.0, 2)

        available_orders.append(
            NearbyOrderResponse(
                order_id=order.id,
                business_name=b_name,
                priority=order.priority,
                pickup_address=order.pickup_address,
                dropoff_address=order.dropoff_address,
                distance_to_pickup_km=pickup_km,
                trip_distance_km=trip_km,
                delivery_fee=float(order.delivery_fee),
                created_at=order.created_at
            )
        )

    return available_orders