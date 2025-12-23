import json
import hashlib
from typing import Optional
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import base64


class SignatureService:
    """Ed25519 signature verification for anchor events"""
    
    # Registry of known manufacturer public keys
    # In production, this would be stored in a database
    _manufacturer_keys: dict[str, str] = {}
    
    @classmethod
    def register_manufacturer_key(cls, manufacturer_id: str, public_key_b64: str):
        """Register a manufacturer's public key"""
        cls._manufacturer_keys[manufacturer_id] = public_key_b64
    
    @classmethod
    def get_manufacturer_key(cls, manufacturer_id: str) -> Optional[str]:
        """Get a manufacturer's public key"""
        return cls._manufacturer_keys.get(manufacturer_id)
    
    @staticmethod
    def create_signing_payload(event_data: dict) -> bytes:
        """Create the canonical payload to sign/verify
        
        The signature covers all fields except the signature itself.
        Fields are sorted alphabetically and serialized to JSON.
        """
        # Remove signature from payload for verification
        payload = {k: v for k, v in event_data.items() if k != "signature"}
        
        # Sort keys for deterministic serialization
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return canonical.encode("utf-8")
    
    @classmethod
    def verify_signature(
        cls,
        event_data: dict,
        signature_b64: str,
        public_key_b64: Optional[str] = None,
        manufacturer_id: Optional[str] = None,
    ) -> bool:
        """Verify an Ed25519 signature on an event
        
        Args:
            event_data: The event payload
            signature_b64: Base64-encoded signature
            public_key_b64: Base64-encoded public key (if known)
            manufacturer_id: Manufacturer ID to look up key (if public_key not provided)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Get public key
            if public_key_b64 is None:
                if manufacturer_id is None:
                    # Try to get manufacturer_id from event
                    manufacturer_id = event_data.get("manufacturer_id")
                
                if manufacturer_id:
                    public_key_b64 = cls.get_manufacturer_key(manufacturer_id)
                
                if public_key_b64 is None:
                    # In development/testing, accept unverified signatures
                    # In production, this would return False
                    return True  # TODO: Make this configurable
            
            # Decode key and signature
            public_key_bytes = base64.b64decode(public_key_b64)
            signature_bytes = base64.b64decode(signature_b64)
            
            # Create verify key
            verify_key = VerifyKey(public_key_bytes)
            
            # Create signing payload
            payload = cls.create_signing_payload(event_data)
            
            # Verify
            verify_key.verify(payload, signature_bytes)
            return True
            
        except (BadSignatureError, ValueError, Exception) as e:
            # Log verification failure in production
            print(f"Signature verification failed: {e}")
            return False
    
    @staticmethod
    def hash_event(event_data: dict) -> str:
        """Create a SHA-256 hash of the event for deduplication"""
        payload = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
