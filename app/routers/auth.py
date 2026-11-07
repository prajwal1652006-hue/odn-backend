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

def get_role_str(role_val) -> str:
    if hasattr(role_val, "value"):
        return str(role_val.value)
    return str(role_val)

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already registered. Please login or try a different number."
        )

    try:
        user_role_enum = UserRole(payload.role.upper())
    except ValueError:
        user_role_enum = UserRole.RIDER

    new_user = User(
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=user_role_enum
    )
    db.add(new_user)
    db.flush()

    if user_role_enum == UserRole.RIDER:
        license_num = payload.license_number or f"DL-{random.randint(100000, 999999)}"
        rider_profile = Rider(
            user_id=new_user.id,
            vehicle_type=VehicleType.BIKE,
            license_number=license_num,
            kyc_status=KYCStatus.VERIFIED
        )
        db.add(rider_profile)

    elif user_role_enum == UserRole.BUSINESS:
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

    role_str = get_role_str(new_user.role)
    access_token = create_access_token(data={"sub": str(new_user.id), "role": role_str})
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        role=role_str,
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

    role_str = get_role_str(user.role)
    access_token = create_access_token(data={"sub": str(user.id), "role": role_str})
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=role_str,
        full_name=user.full_name
    )

@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        target_role_str = payload.role.upper()
        target_role_enum = UserRole.BUSINESS if target_role_str == "BUSINESS" else UserRole.RIDER

        random_suffix = random.randint(100000, 999999)
        role_prefix = "88" if target_role_enum == UserRole.BUSINESS else "99"
        synthetic_phone = f"+91{role_prefix}{random_suffix}"

        user = User(
            phone_number=synthetic_phone,
            password_hash=hash_password("GoogleAuthPass2026"),
            full_name=f"Google Partner ({target_role_str.title()})",
            role=target_role_enum
        )
        db.add(user)
        db.flush()

        if target_role_enum == UserRole.RIDER:
            rider_profile = Rider(
                user_id=user.id,
                vehicle_type=VehicleType.BIKE,
                license_number=f"KA-GOOG-{random_suffix}",
                kyc_status=KYCStatus.VERIFIED
            )
            db.add(rider_profile)
        else:
            pickup_geom = WKTElement("POINT(77.6408 12.9783)", srid=4326)
            business_profile = Business(
                user_id=user.id,
                business_name="Google Partner Hub",
                business_category="RESTAURANT",
                pickup_address="Indiranagar 100ft Rd, Bengaluru",
                pickup_location=pickup_geom,
                contact_phone=synthetic_phone
            )
            db.add(business_profile)

        db.commit()
        db.refresh(user)

        role_str = get_role_str(user.role)
        access_token = create_access_token(data={"sub": str(user.id), "role": role_str})
        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            role=role_str,
            full_name=user.full_name
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google auth error: {str(e)}"
        )

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user