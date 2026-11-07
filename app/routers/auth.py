import random
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.database import get_db
from app.models.user import User, UserRole
from app.models.rider import Rider, VehicleType, KYCStatus
from app.models.business import Business
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, GoogleLoginRequest, TokenResponse, UserProfileResponse
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already registered"
        )

    new_user = User(
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role
    )
    db.add(new_user)
    db.flush()

    if payload.role == UserRole.RIDER:
        license_num = payload.license_number or f"DL-{random.randint(100000, 999999)}"
        rider_profile = Rider(
            user_id=new_user.id,
            vehicle_type=payload.vehicle_type or VehicleType.BIKE,
            license_number=license_num,
            kyc_status=KYCStatus.VERIFIED
        )
        db.add(rider_profile)

    elif payload.role == UserRole.BUSINESS:
        store_name = payload.business_name or f"{payload.full_name}'s Store"
        category = payload.business_category or "GROCERY"
        address = payload.pickup_address or "Indiranagar 100ft Rd, Bengaluru"
        lat = payload.pickup_latitude or 12.9783
        lng = payload.pickup_longitude or 77.6408

        pickup_geom = WKTElement(f"POINT({lng} {lat})", srid=4326)
        business_profile = Business(
            user_id=new_user.id,
            business_name=store_name,
            business_category=category,
            pickup_address=address,
            pickup_location=pickup_geom,
            contact_phone=payload.phone_number
        )
        db.add(business_profile)

    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role.value})
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        role=new_user.role,
        full_name=new_user.full_name
    )

@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role,
        full_name=user.full_name
    )

@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # Resolve role enum cleanly
        target_role = UserRole.BUSINESS if payload.role.upper() == "BUSINESS" else UserRole.RIDER

        # Deterministic phone number per role for testing
        role_tag = "99" if target_role == UserRole.RIDER else "88"
        synthetic_phone = f"+9198{role_tag}001122"

        user = db.query(User).filter(User.phone_number == synthetic_phone).first()

        if not user:
            user = User(
                phone_number=synthetic_phone,
                password_hash=hash_password("GoogleAuth2026!"),
                full_name="Google Partner User",
                role=target_role
            )
            db.add(user)
            db.flush()

            if target_role == UserRole.RIDER:
                rider_profile = Rider(
                    user_id=user.id,
                    vehicle_type=VehicleType.BIKE,
                    license_number="KA-GOOG-9988",
                    kyc_status=KYCStatus.VERIFIED
                )
                db.add(rider_profile)
            else:
                pickup_geom = WKTElement("POINT(77.6408 12.9783)", srid=4326)
                business_profile = Business(
                    user_id=user.id,
                    business_name="Google Store Hub",
                    business_category="RESTAURANT",
                    pickup_address="Indiranagar 100ft Rd, Bengaluru",
                    pickup_location=pickup_geom,
                    contact_phone=synthetic_phone
                )
                db.add(business_profile)

            db.commit()
            db.refresh(user)

        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            role=user.role,
            full_name=user.full_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google login engine error: {str(e)}")

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
