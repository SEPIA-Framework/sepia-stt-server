"""Authenticate and handle users"""

import time
from fastapi import WebSocket

# For now we just use a simple static token.
# TODO: Replace with user list
COMMON_TOKEN = "test123"

class SessionIds:
    """Generate session IDs"""
    last_session_id = 0

    @staticmethod
    def get_new_sesstion_id():
        """Generate new session ID"""
        SessionIds.last_session_id += 1
        if SessionIds.last_session_id > 9999:
            SessionIds.last_session_id = 1
        return f"{SessionIds.last_session_id}-{int(time.time())}"

class SocketUser:
    """Class representing a user with some basic info and auth. method"""
    def __init__(self, websocket: WebSocket):
        self.is_authenticated = False
        self.socket = websocket
        self.session_id = SessionIds.get_new_sesstion_id()

    async def authenticate(self, client_id, token):
        """Check if user is valid"""
        if client_id is not None and token == COMMON_TOKEN:
            self.is_authenticated = True
