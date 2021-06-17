"""Module to handle HTTP API calls like settings etc."""

from fastapi import Response, status
from pydantic import BaseModel

from launch import get_settings_response

class SettingsRequest(BaseModel):
    """Request to modify server settings"""
    lang: str = "en"

class HttpApiEndpoint:
    """HTTP endpoint handler"""
    def handle_settings_req_get(self):
        """Handle settings GET request"""
        return {
            "result": "success",
            "settings": get_settings_response()
        }
    async def handle_settings_req_post(self, req: SettingsRequest, response: Response):
        """Handle settings POST request"""
        response.status_code=status.HTTP_501_NOT_IMPLEMENTED
        return ""
