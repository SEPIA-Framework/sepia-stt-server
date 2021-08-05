"""Module to handle HTTP API calls like settings etc."""

from fastapi import Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from launch import get_settings_response

class SettingsRequest(BaseModel):
    """Request to modify server settings"""
    language: str = "de-DE"

class HttpApiEndpoint:
    """HTTP endpoint handler"""

    def handle_settings_req_get(self):
        """Handle settings GET request"""
        data = {
            "result": "success",
            "settings": get_settings_response()
        }
        response = JSONResponse(content=data)
        return response

    def handle_settings_req_post(self, req: SettingsRequest, response: Response):
        """Handle settings POST request"""
        response = JSONResponse({"error": (
            "Not implemented. "
            "Please use WebSocket 'welcome' message for session settings instead."
        )})
        response.status_code=status.HTTP_501_NOT_IMPLEMENTED
        return response
