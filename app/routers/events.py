from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from pydantic import ValidationError

from app.database import get_db
from app.models.anchor_event import AnchorEvent
from app.schemas.events import (
    EventType,
    AnchorRegisteredEvent,
    AnchorSealArmedEvent,
    AnchorSealBrokenEvent,
    AnchorEnvironmentalAlertEvent,
    AnchorCustodySignalEvent,
    AnchorEventResponse,
    AnchorEventListResponse,
)
from app.services.event_processor import EventProcessor

router = APIRouter()


def parse_event(data: dict):
    """Parse incoming event based on event_type"""
    event_type = data.get("event_type")
    
    if event_type == EventType.ANCHOR_REGISTERED:
        return AnchorRegisteredEvent(**data)
    elif event_type == EventType.ANCHOR_SEAL_ARMED:
        return AnchorSealArmedEvent(**data)
    elif event_type == EventType.ANCHOR_SEAL_BROKEN:
        return AnchorSealBrokenEvent(**data)
    elif event_type == EventType.ANCHOR_ENVIRONMENTAL_ALERT:
        return AnchorEnvironmentalAlertEvent(**data)
    elif event_type == EventType.ANCHOR_CUSTODY_SIGNAL:
        return AnchorCustodySignalEvent(**data)
    else:
        raise ValueError(f"Unknown event type: {event_type}")


@router.post(
    "/events",
    response_model=AnchorEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_event(
    event_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Ingest an anchor event
    
    This is the primary endpoint for anchor hardware to submit events.
    Events must be signed with Ed25519 and include a valid schema_version.
    
    Only 5 event types are accepted:
    - ANCHOR_REGISTERED
    - ANCHOR_SEAL_ARMED
    - ANCHOR_SEAL_BROKEN
    - ANCHOR_ENVIRONMENTAL_ALERT
    - ANCHOR_CUSTODY_SIGNAL
    """
    # Validate event_type exists
    if "event_type" not in event_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="event_type is required",
        )
    
    # Validate event_type is in canonical set
    try:
        event_type = EventType(event_data["event_type"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown event type: {event_data['event_type']}. "
                   f"Valid types: {[e.value for e in EventType]}",
        )
    
    # Parse and validate event
    try:
        event = parse_event(event_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Process event
    processor = EventProcessor(db)
    db_event = await processor.process_event(event)
    
    return AnchorEventResponse(
        id=db_event.id,
        event_type=db_event.event_type,
        anchor_id=db_event.anchor_id,
        signature_verified=db_event.signature_verified,
        ledger_synced=db_event.ledger_synced,
        received_at=db_event.received_at,
    )


@router.get(
    "/events/{event_id}",
    response_model=AnchorEventResponse,
)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific event by ID"""
    from uuid import UUID
    
    try:
        uuid_id = UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID format",
        )
    
    result = await db.execute(
        select(AnchorEvent).where(AnchorEvent.id == uuid_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    return AnchorEventResponse(
        id=event.id,
        event_type=event.event_type,
        anchor_id=event.anchor_id,
        signature_verified=event.signature_verified,
        ledger_synced=event.ledger_synced,
        received_at=event.received_at,
    )
