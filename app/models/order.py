import enum
import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Enum, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from app.database import Base

class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    ARRIVED_AT_PICKUP = "ARRIVED_AT_PICKUP"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class OrderPriority(str, enum.Enum):
    STANDARD = "STANDARD"
    HIGH = "HIGH"
    EXPRESS = "EXPRESS"

class PayoutStatus(str, enum.Enum):
    ACCUMULATED = "ACCUMULATED"
    PAID_OUT = "PAID_OUT"

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("riders.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(OrderStatus, name="order_status"), default=OrderStatus.CREATED, nullable=False)
    priority = Column(Enum(OrderPriority, name="order_priority"), default=OrderPriority.STANDARD, nullable=False)
    pickup_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    pickup_address = Column(Text, nullable=False)
    dropoff_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    dropoff_address = Column(Text, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    delivery_fee = Column(Numeric(8, 2), nullable=False)
    otp_code = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

class OrderOffer(Base):
    __tablename__ = "order_offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(5, 4), nullable=False)
    offered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('order_id', 'rider_id', name='unique_active_offer'),
    )

class EarningsLedger(Base):
    __tablename__ = "earnings_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("riders.id", ondelete="RESTRICT"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False)
    base_payout = Column(Numeric(8, 2), nullable=False)
    surge_bonus = Column(Numeric(8, 2), default=0.00, nullable=False)
    total_payout = Column(Numeric(8, 2), nullable=False)
    payout_status = Column(Enum(PayoutStatus, name="payout_status"), default=PayoutStatus.ACCUMULATED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)