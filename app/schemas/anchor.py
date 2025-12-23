from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class AnchorStatus(str, Enum):
    ACTIVE = "active"
    SEALED = "sealed"
    BREACHED = "breached"
    INACTIVE = "inactive"


class CertificationTier(str, Enum):
    COMPATIBLE = "compatible"  # Tier 1
    NATIVE = "native"          # Tier 2
    VERIFIED = "verified"      # Tier 3


class AnchorResponse(BaseModel):
    """Anchor status response"""
    id: UUID
    anchor_id: str
    asset_id: Optional[UUID]
    
    hardware_model: str
    firmware_version: str
    manufacturer_id: str
    
    status: AnchorStatus
    certification_tier: CertificationTier
    current_seal_id: Optional[str]
    
    registered_at: datetime
    last_event_at: Optional[datetime]
    
    is_revoked: bool
    
    class Config:
        from_attributes = True


class AnchorListResponse(BaseModel):
    """List of anchors"""
    anchors: list[AnchorResponse]
    total: int
