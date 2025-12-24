import httpx
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class LedgerService:
    """Client for writing events to PROVENIQ Ledger"""
    
    def __init__(self):
        self.base_url = settings.ledger_api_url
        self.api_key = settings.ledger_api_key
    
    async def write_event(
        self,
        event_type: str,
        anchor_id: str,
        asset_id: Optional[UUID],
        payload: dict,
        event_timestamp: datetime,
    ) -> Optional[UUID]:
        """Write an anchor event to the Ledger
        
        Args:
            event_type: The canonical event type
            anchor_id: The anchor hardware ID
            asset_id: The associated asset ID (if any)
            payload: The full event payload
            event_timestamp: When the event occurred
            
        Returns:
            The Ledger event ID if successful, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/events",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "event_type": event_type,
                        "source": "anchors",
                        "anchor_id": anchor_id,
                        "asset_id": str(asset_id) if asset_id else None,
                        "payload": payload,
                        "event_timestamp": event_timestamp.isoformat(),
                    },
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return UUID(data.get("event_id"))
                else:
                    print(f"Ledger write failed: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.RequestError as e:
            print(f"Ledger connection error: {e}")
            return None
        except Exception as e:
            print(f"Ledger write error: {e}")
            return None
    
    async def get_anchor_history(
        self,
        anchor_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get event history for an anchor from the Ledger
        
        Args:
            anchor_id: The anchor hardware ID
            limit: Max events to return
            offset: Pagination offset
            
        Returns:
            List of events from the Ledger
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/events",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    params={
                        "source": "anchors",
                        "anchor_id": anchor_id,
                        "limit": limit,
                        "offset": offset,
                    },
                )
                
                if response.status_code == 200:
                    return response.json().get("events", [])
                else:
                    return []
                    
        except Exception as e:
            print(f"Ledger read error: {e}")
            return []


# Singleton instance
ledger_service = LedgerService()
