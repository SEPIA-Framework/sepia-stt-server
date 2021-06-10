"""Different socket message classes for convenience"""

from typing import Optional

from pydantic import BaseModel

from launch import settings, SERVER_VERSION

class MessageIds:
    """Generate message IDs"""
    last_message_id = 0

    @staticmethod
    def get_new_message_id():
        """Generate new message ID"""
        MessageIds.last_message_id += 1
        # set some limit since each user has his own scope anyway
        if MessageIds.last_message_id > 999999:
            MessageIds.last_message_id = 1
        return MessageIds.last_message_id

class SocketJsonMessage(BaseModel):
    """Incoming socket message in JSON format"""
    type: str   # for example: "welcome"
    data: Optional[dict] = None
    access_token: Optional[str] = None
    client_id: Optional[str] = None
    msg_id: int
    #{"type": "welcome", "data": { "language": "en-US", "model": "...", "grammar": "..." }, "access_token": "", "client_id": "", "ts": 1620804751062, "msg_id": 1 }

class SocketMessage():
    """Default socket message"""
    def __init__(self, msg_type, msg_id = None):
        if msg_id is None:
            msg_id = MessageIds.get_new_message_id()
        self.json = {
            "type": msg_type,
            "msg_id": msg_id,
            "code": 200
        }
    def set_field(self, field, value):
        """Set specific field of message"""
        self.json[field] = value

class SocketPingMessage(SocketMessage):
    """Ping message to check if client is alive"""
    def __init__(self, msg_id):
        super().__init__("ping", msg_id)

class SocketWelcomeMessage(SocketMessage):
    """Welcome message (sent after authentication)"""
    def __init__(self, msg_id):
        super().__init__("welcome", msg_id)
        self.set_field("info", {
            "version": SERVER_VERSION,
            "engine": settings.asr_engine,
            "models": settings.asr_model_paths,
            "more": "tbd"
            # add e.g.: languages, engine, models, features...
        })

class SocketBroadcastMessage(SocketMessage):
    """Socket message for broadcasting"""
    def __init__(self, msg_type, data):
        super().__init__(msg_type)
        self.set_field("data", data)

class SocketErrorMessage(SocketMessage):
    """Socket error message"""
    def __init__(self, code, name, message):
        super().__init__("error")
        self.set_field("code", code)
        self.set_field("name", name)
        self.set_field("message", message)

