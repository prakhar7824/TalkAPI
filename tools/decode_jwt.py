"""decode_jwt tool - JWT decoder with expiration checking (TalkAPI by RAJ)"""

import json
import base64
from typing import Any, Dict
from datetime import datetime
from mcp.types import Tool


class DecodeJWTTool:
    """Tool for decoding JWT tokens (without verification)"""
    
    def get_definition(self) -> Tool:
        """Return tool definition for MCP"""
        return Tool(
            name="decode_jwt",
            description=(
                "Decode a JWT token without verification. "
                "Extracts the payload (user info, expiration, etc.) and checks if the token is expired. "
                "This is useful for debugging authentication flows. "
                "Note: This does NOT verify the token signature (no secret key required)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "JWT token string (with or without 'Bearer ' prefix)",
                    },
                },
                "required": ["token"],
            },
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Decode JWT and check expiration"""
        token = arguments.get("token", "").strip()
        
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        if not token:
            return json.dumps({
                "error": "Empty token provided",
            }, indent=2)
        
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                return json.dumps({
                    "error": "Invalid JWT format (expected 3 parts separated by dots)",
                }, indent=2)
            
            # Decode header
            header_padded = parts[0] + "=" * (4 - len(parts[0]) % 4)
            header_bytes = base64.urlsafe_b64decode(header_padded)
            header = json.loads(header_bytes)
            
            # Decode payload
            payload_padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_padded)
            payload = json.loads(payload_bytes)
            
            # Check expiration
            exp = payload.get("exp")
            is_expired = False
            expires_at = None
            expires_in = None
            
            if exp:
                expires_at = datetime.fromtimestamp(exp)
                now = datetime.now()
                is_expired = expires_at < now
                if not is_expired:
                    expires_in = (expires_at - now).total_seconds()
            
            result = {
                "header": header,
                "payload": payload,
                "is_expired": is_expired,
            }
            
            if expires_at:
                result["expires_at"] = expires_at.isoformat()
                if expires_in:
                    result["expires_in_seconds"] = int(expires_in)
                    hours = expires_in / 3600
                    result["expires_in_hours"] = round(hours, 2)
            
            if is_expired:
                result["warning"] = "⚠️ Token is EXPIRED"
            
            return json.dumps(result, indent=2, default=str)
        
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Failed to decode JWT: {str(e)}",
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": f"Error processing JWT: {str(e)}",
            }, indent=2)

