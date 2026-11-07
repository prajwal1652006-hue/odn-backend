import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from app.database import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(120), nullable=False)
    business_category = Column(String(50), nullable=False)
    pickup_address = Column(Text, nullable=False)
    pickup_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    contact_phone = Column(String(15), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)