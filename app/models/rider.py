import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from app.database import Base

class VehicleType(str, enum.Enum):
    BIKE = "BIKE"
    EV_SCOOTER = "EV_SCOOTER"
    BICYCLE = "BICYCLE"

class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class Rider(Base):
    __tablename__ = "riders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    vehicle_type = Column(Enum(VehicleType, name="vehicle_type"), default=VehicleType.BIKE, nullable=False)
    license_number = Column(String(50), nullable=False)
    kyc_status = Column(Enum(KYCStatus, name="kyc_status"), default=KYCStatus.PENDING, nullable=False)
    is_online = Column(Boolean, default=False, nullable=False)
    current_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)