from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Union
from datetime import datetime
from uuid import UUID
from enum import Enum


class EventType(str, Enum):
    ANCHOR_REGISTERED = "ANCHOR_REGISTERED"
    ANCHOR_SEAL_ARMED = "ANCHOR_SEAL_ARMED"
    ANCHOR_SEAL_BROKEN = "ANCHOR_SEAL_BROKEN"
    ANCHOR_ENVIRONMENTAL_ALERT = "ANCHOR_ENVIRONMENTAL_ALERT"
    ANCHOR_CUSTODY_SIGNAL = "ANCHOR_CUSTODY_SIGNAL"


class TriggerType(str, Enum):
    MANUAL = "MANUAL"
    FORCE = "FORCE"
    TAMPER = "TAMPER"
    UNKNOWN = "UNKNOWN"


class EnvironmentalMetric(str, Enum):
    SHOCK = "SHOCK"
    TEMP = "TEMP"
    HUMIDITY = "HUMIDITY"


class CustodyDirection(str, Enum):
    RELEASE = "RELEASE"
    ACCEPT = "ACCEPT"


class GeoCoordinate(BaseModel):
    lat_e7: int = Field(..., description="Latitude × 10^7 (integer)")
    lon_e7: int = Field(..., description="Longitude × 10^7 (integer)")
    
    @field_validator("lat_e7")
    @classmethod
    def validate_lat(cls, v):
        if not -900000000 <= v <= 900000000:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v
    
    @field_validator("lon_e7")
    @classmethod
    def validate_lon(cls, v):
        if not -1800000000 <= v <= 1800000000:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v


class AnchorEventBase(BaseModel):
    """Base schema for all anchor events"""
    anchor_id: str = Field(..., min_length=1, max_length=64)
    timestamp: datetime
    signature: str = Field(..., min_length=1, description="Ed25519 signature")
    schema_version: str = Field(default="1.0.0")


class AnchorRegisteredEvent(AnchorEventBase):
    """ANCHOR_REGISTERED: Bind hardware → asset"""
    event_type: Literal[EventType.ANCHOR_REGISTERED] = EventType.ANCHOR_REGISTERED
    asset_id: UUID
    hardware_model: str = Field(..., min_length=1, max_length=128)
    firmware_version: str = Field(..., min_length=1, max_length=32)
    manufacturer_id: str = Field(..., min_length=1, max_length=64)


class AnchorSealArmedEvent(AnchorEventBase):
    """ANCHOR_SEAL_ARMED: Declare asset is sealed/locked"""
    event_type: Literal[EventType.ANCHOR_SEAL_ARMED] = EventType.ANCHOR_SEAL_ARMED
    seal_id: str = Field(..., min_length=1, max_length=64)
    geo: GeoCoordinate


class AnchorSealBrokenEvent(AnchorEventBase):
    """ANCHOR_SEAL_BROKEN: Irreversible integrity breach"""
    event_type: Literal[EventType.ANCHOR_SEAL_BROKEN] = EventType.ANCHOR_SEAL_BROKEN
    seal_id: str = Field(..., min_length=1, max_length=64)
    trigger_type: TriggerType
    geo: GeoCoordinate


class AnchorEnvironmentalAlertEvent(AnchorEventBase):
    """ANCHOR_ENVIRONMENTAL_ALERT: Condition exposure evidence"""
    event_type: Literal[EventType.ANCHOR_ENVIRONMENTAL_ALERT] = EventType.ANCHOR_ENVIRONMENTAL_ALERT
    metric: EnvironmentalMetric
    value: str = Field(..., min_length=1, max_length=64)
    threshold: str = Field(..., min_length=1, max_length=64)


class AnchorCustodySignalEvent(AnchorEventBase):
    """ANCHOR_CUSTODY_SIGNAL: Physical custody handoff"""
    event_type: Literal[EventType.ANCHOR_CUSTODY_SIGNAL] = EventType.ANCHOR_CUSTODY_SIGNAL
    challenge_id: UUID
    direction: CustodyDirection
    counterparty_pubkey: str = Field(..., min_length=1, max_length=128)


# Union type for event ingestion
AnchorEventCreate = Union[
    AnchorRegisteredEvent,
    AnchorSealArmedEvent,
    AnchorSealBrokenEvent,
    AnchorEnvironmentalAlertEvent,
    AnchorCustodySignalEvent,
]


class AnchorEventResponse(BaseModel):
    """Response after event ingestion"""
    id: UUID
    event_type: EventType
    anchor_id: str
    signature_verified: bool
    ledger_synced: bool
    received_at: datetime
    
    class Config:
        from_attributes = True


class AnchorEventListResponse(BaseModel):
    """List of events for an anchor"""
    anchor_id: str
    events: list[AnchorEventResponse]
    total: int
