"""Module to handle HTTP API calls like settings etc."""

from fastapi import Response, status
from pydantic import BaseModel

class Languages:
    """Available languages given as ISO 639-1 codes used by SEPIA"""
    DE = "de"
    EN = "en"

class SettingsRequest(BaseModel):
    """Request to modify server settings"""
    lang: str = "en"

class HttpApiEndpoint:
    """HTTP endpoint handler"""
    async def handle_settings_req(self, req: SettingsRequest, response: Response):
        """Handle settings request"""
        response.status_code=status.HTTP_501_NOT_IMPLEMENTED
        return ""
        