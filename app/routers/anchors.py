from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models.anchor import Anchor
from app.models.anchor_event import AnchorEvent
from app.schemas.anchor import AnchorResponse, AnchorListResponse
from app.schemas.events import AnchorEventResponse, AnchorEventListResponse

router = APIRouter()


@router.get(
    "/anchors/{anchor_id}",
    response_model=AnchorResponse,
)
async def get_anchor(
    anchor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get anchor status by hardware ID"""
    result = await db.execute(
        select(Anchor).where(Anchor.anchor_id == anchor_id)
    )
    anchor = result.scalar_one_or_none()
    
    if not anchor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anchor not found: {anchor_id}",
        )
    
    return anchor


@router.get(
    "/anchors/{anchor_id}/events",
    response_model=AnchorEventListResponse,
)
async def get_anchor_events(
    anchor_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get event history for an anchor"""
    # Verify anchor exists
    result = await db.execute(
        select(Anchor).where(Anchor.anchor_id == anchor_id)
    )
    anchor = result.scalar_one_or_none()
    
    if not anchor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anchor not found: {anchor_id}",
        )
    
    # Get events
    result = await db.execute(
        select(AnchorEvent)
        .where(AnchorEvent.anchor_id == anchor_id)
        .order_by(desc(AnchorEvent.event_timestamp))
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(
        select(AnchorEvent)
        .where(AnchorEvent.anchor_id == anchor_id)
    )
    total = len(count_result.scalars().all())
    
    return AnchorEventListResponse(
        anchor_id=anchor_id,
        events=[
            AnchorEventResponse(
                id=e.id,
                event_type=e.event_type,
                anchor_id=e.anchor_id,
                signature_verified=e.signature_verified,
                ledger_synced=e.ledger_synced,
                received_at=e.received_at,
            )
            for e in events
        ],
        total=total,
    )


@router.get(
    "/assets/{asset_id}/anchors",
    response_model=AnchorListResponse,
)
async def get_anchors_for_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all anchors associated with an asset"""
    result = await db.execute(
        select(Anchor).where(Anchor.asset_id == asset_id)
    )
    anchors = result.scalars().all()
    
    return AnchorListResponse(
        anchors=anchors,
        total=len(anchors),
    )


@router.get(
    "/manufacturers/{manufacturer_id}/anchors",
    response_model=AnchorListResponse,
)
async def get_anchors_by_manufacturer(
    manufacturer_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get all anchors from a specific manufacturer"""
    result = await db.execute(
        select(Anchor)
        .where(Anchor.manufacturer_id == manufacturer_id)
        .limit(limit)
        .offset(offset)
    )
    anchors = result.scalars().all()
    
    # Get total
    count_result = await db.execute(
        select(Anchor).where(Anchor.manufacturer_id == manufacturer_id)
    )
    total = len(count_result.scalars().all())
    
    return AnchorListResponse(
        anchors=anchors,
        total=total,
    )
