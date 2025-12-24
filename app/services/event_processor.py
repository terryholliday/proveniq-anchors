from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import UUID
from typing import Union

from app.models.anchor import Anchor, AnchorStatus
from app.models.anchor_event import AnchorEvent, AnchorEventType
from app.schemas.events import (
    AnchorRegisteredEvent,
    AnchorSealArmedEvent,
    AnchorSealBrokenEvent,
    AnchorEnvironmentalAlertEvent,
    AnchorCustodySignalEvent,
)
from app.services.signature import SignatureService
from app.services.ledger import ledger_service


AnchorEventInput = Union[
    AnchorRegisteredEvent,
    AnchorSealArmedEvent,
    AnchorSealBrokenEvent,
    AnchorEnvironmentalAlertEvent,
    AnchorCustodySignalEvent,
]


class EventProcessor:
    """Process incoming anchor events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_event(self, event: AnchorEventInput) -> AnchorEvent:
        """Process and store an anchor event
        
        1. Verify signature
        2. Store event
        3. Update anchor state
        4. Write to Ledger
        
        Args:
            event: The validated event input
            
        Returns:
            The stored AnchorEvent record
        """
        # Convert to dict for processing
        event_data = event.model_dump(mode="json")
        
        # Verify signature
        signature_verified = SignatureService.verify_signature(
            event_data,
            event.signature,
            manufacturer_id=getattr(event, "manufacturer_id", None),
        )
        
        # Create event record
        db_event = await self._store_event(event, event_data, signature_verified)
        
        # Update anchor state based on event type
        await self._update_anchor_state(event)
        
        # Write to Ledger (async, don't block)
        await self._sync_to_ledger(db_event, event_data)
        
        await self.db.commit()
        await self.db.refresh(db_event)
        
        return db_event
    
    async def _store_event(
        self,
        event: AnchorEventInput,
        event_data: dict,
        signature_verified: bool,
    ) -> AnchorEvent:
        """Store the event in the database"""
        
        # Base fields
        db_event = AnchorEvent(
            event_type=AnchorEventType(event.event_type.value),
            anchor_id=event.anchor_id,
            schema_version=event.schema_version,
            event_timestamp=event.timestamp,
            signature=event.signature,
            signature_verified=signature_verified,
            raw_payload=event_data,
        )
        
        # Event-specific fields
        if isinstance(event, AnchorRegisteredEvent):
            db_event.asset_id = event.asset_id
            db_event.hardware_model = event.hardware_model
            db_event.firmware_version = event.firmware_version
            db_event.manufacturer_id = event.manufacturer_id
            
        elif isinstance(event, AnchorSealArmedEvent):
            db_event.seal_id = event.seal_id
            db_event.geo_lat_e7 = event.geo.lat_e7
            db_event.geo_lon_e7 = event.geo.lon_e7
            
        elif isinstance(event, AnchorSealBrokenEvent):
            db_event.seal_id = event.seal_id
            db_event.trigger_type = event.trigger_type
            db_event.geo_lat_e7 = event.geo.lat_e7
            db_event.geo_lon_e7 = event.geo.lon_e7
            
        elif isinstance(event, AnchorEnvironmentalAlertEvent):
            db_event.metric = event.metric
            db_event.metric_value = event.value
            db_event.metric_threshold = event.threshold
            
        elif isinstance(event, AnchorCustodySignalEvent):
            db_event.challenge_id = event.challenge_id
            db_event.custody_direction = event.direction
            db_event.counterparty_pubkey = event.counterparty_pubkey
        
        self.db.add(db_event)
        await self.db.flush()
        
        return db_event
    
    async def _update_anchor_state(self, event: AnchorEventInput):
        """Update anchor state based on event type"""
        
        if isinstance(event, AnchorRegisteredEvent):
            # Create or update anchor record
            result = await self.db.execute(
                select(Anchor).where(Anchor.anchor_id == event.anchor_id)
            )
            anchor = result.scalar_one_or_none()
            
            if anchor is None:
                anchor = Anchor(
                    anchor_id=event.anchor_id,
                    asset_id=event.asset_id,
                    hardware_model=event.hardware_model,
                    firmware_version=event.firmware_version,
                    manufacturer_id=event.manufacturer_id,
                    public_key="",  # Set during certification
                    status=AnchorStatus.ACTIVE,
                )
                self.db.add(anchor)
            else:
                # Update existing anchor
                anchor.asset_id = event.asset_id
                anchor.firmware_version = event.firmware_version
            
            anchor.last_event_at = event.timestamp
            
        elif isinstance(event, AnchorSealArmedEvent):
            result = await self.db.execute(
                select(Anchor).where(Anchor.anchor_id == event.anchor_id)
            )
            anchor = result.scalar_one_or_none()
            
            if anchor:
                anchor.status = AnchorStatus.SEALED
                anchor.current_seal_id = event.seal_id
                anchor.last_event_at = event.timestamp
                
        elif isinstance(event, AnchorSealBrokenEvent):
            result = await self.db.execute(
                select(Anchor).where(Anchor.anchor_id == event.anchor_id)
            )
            anchor = result.scalar_one_or_none()
            
            if anchor:
                anchor.status = AnchorStatus.BREACHED
                anchor.current_seal_id = None  # Seal is broken
                anchor.last_event_at = event.timestamp
                
        else:
            # Update last_event_at for other events
            result = await self.db.execute(
                select(Anchor).where(Anchor.anchor_id == event.anchor_id)
            )
            anchor = result.scalar_one_or_none()
            
            if anchor:
                anchor.last_event_at = event.timestamp
    
    async def _sync_to_ledger(self, db_event: AnchorEvent, event_data: dict):
        """Write event to the Ledger"""
        try:
            ledger_event_id = await ledger_service.write_event(
                event_type=db_event.event_type.value,
                anchor_id=db_event.anchor_id,
                asset_id=db_event.asset_id,
                payload=event_data,
                event_timestamp=db_event.event_timestamp,
            )
            
            if ledger_event_id:
                db_event.ledger_synced = True
                db_event.ledger_event_id = ledger_event_id
                db_event.ledger_synced_at = datetime.utcnow()
            
            db_event.processed = True
            
        except Exception as e:
            db_event.processing_error = str(e)
