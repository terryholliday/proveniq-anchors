from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Integer, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class AnchorEventType(str, enum.Enum):
    ANCHOR_REGISTERED = "ANCHOR_REGISTERED"
    ANCHOR_SEAL_ARMED = "ANCHOR_SEAL_ARMED"
    ANCHOR_SEAL_BROKEN = "ANCHOR_SEAL_BROKEN"
    ANCHOR_ENVIRONMENTAL_ALERT = "ANCHOR_ENVIRONMENTAL_ALERT"
    ANCHOR_CUSTODY_SIGNAL = "ANCHOR_CUSTODY_SIGNAL"


class TriggerType(str, enum.Enum):
    MANUAL = "MANUAL"
    FORCE = "FORCE"
    TAMPER = "TAMPER"
    UNKNOWN = "UNKNOWN"


class EnvironmentalMetric(str, enum.Enum):
    SHOCK = "SHOCK"
    TEMP = "TEMP"
    HUMIDITY = "HUMIDITY"


class CustodyDirection(str, enum.Enum):
    RELEASE = "RELEASE"
    ACCEPT = "ACCEPT"


class AnchorEvent(Base):
    __tablename__ = "anchor_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_type = Column(SQLEnum(AnchorEventType), nullable=False, index=True)
    anchor_id = Column(String(64), nullable=False, index=True)
    schema_version = Column(String(16), nullable=False, default="1.0.0")
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Cryptographic signature
    signature = Column(Text, nullable=False)
    signature_verified = Column(Boolean, default=False)
    
    # Event-specific data
    asset_id = Column(UUID(as_uuid=True), nullable=True)
    seal_id = Column(String(64), nullable=True)
    
    # Geo data (stored as integers: lat/lon × 10^7)
    geo_lat_e7 = Column(Integer, nullable=True)
    geo_lon_e7 = Column(Integer, nullable=True)
    
    # Trigger type (for SEAL_BROKEN)
    trigger_type = Column(SQLEnum(TriggerType), nullable=True)
    
    # Environmental data
    metric = Column(SQLEnum(EnvironmentalMetric), nullable=True)
    metric_value = Column(String(64), nullable=True)
    metric_threshold = Column(String(64), nullable=True)
    
    # Custody data
    challenge_id = Column(UUID(as_uuid=True), nullable=True)
    custody_direction = Column(SQLEnum(CustodyDirection), nullable=True)
    counterparty_pubkey = Column(String(128), nullable=True)
    
    # Hardware info (for REGISTERED events)
    hardware_model = Column(String(128), nullable=True)
    firmware_version = Column(String(32), nullable=True)
    manufacturer_id = Column(String(64), nullable=True)
    
    # Full raw payload (for audit)
    raw_payload = Column(JSON, nullable=False)
    
    # Ledger sync status
    ledger_synced = Column(Boolean, default=False)
    ledger_event_id = Column(UUID(as_uuid=True), nullable=True)
    ledger_synced_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
