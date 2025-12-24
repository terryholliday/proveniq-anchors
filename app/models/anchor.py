from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class AnchorStatus(str, enum.Enum):
    ACTIVE = "active"
    SEALED = "sealed"
    BREACHED = "breached"
    INACTIVE = "inactive"


class CertificationTier(str, enum.Enum):
    COMPATIBLE = "compatible"  # Tier 1
    NATIVE = "native"          # Tier 2
    VERIFIED = "verified"      # Tier 3


class Anchor(Base):
    __tablename__ = "anchors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anchor_id = Column(String(64), unique=True, nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Hardware info
    hardware_model = Column(String(128), nullable=False)
    firmware_version = Column(String(32), nullable=False)
    manufacturer_id = Column(String(64), nullable=False, index=True)
    public_key = Column(String(128), nullable=False)
    
    # Status
    status = Column(SQLEnum(AnchorStatus), default=AnchorStatus.ACTIVE, nullable=False)
    certification_tier = Column(SQLEnum(CertificationTier), default=CertificationTier.COMPATIBLE, nullable=False)
    
    # Current seal (if any)
    current_seal_id = Column(String(64), nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Soft delete
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(256), nullable=True)
