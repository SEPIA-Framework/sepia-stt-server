"""Different socket message classes for convenience"""

from typing import Optional

from pydantic import BaseModel

from launch import get_settings_response

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

class SocketJsonInputMessage(BaseModel):
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

class SocketResponseMessage(SocketMessage):
    """Ping message to check if client is alive"""
    def __init__(self, msg_id, response_text = None, data = None):
        super().__init__("response", msg_id)
        if response_text is not None:
            self.set_field("response", response_text)
        if data is not None:
            self.set_field("data", data)

class SocketWelcomeMessage(SocketMessage):
    """Welcome message (sent after authentication)"""
    def __init__(self, msg_id, processor_options = None):
        super().__init__("welcome", msg_id)
        info = get_settings_response()
        if processor_options:
            info["options"] = processor_options
        self.set_field("info", info)

class SocketTranscriptMessage(SocketMessage):
    """Result message to be sent for example when ASR engine transcribed audio etc."""
    def __init__(self, transcript, is_final, confidence = -1, features = None, alternatives = None):
        super().__init__("result")
        self.set_field("transcript", transcript)
        self.set_field("isFinal", is_final)
        if confidence >= 0:
            self.set_field("confidence", confidence)
        if features is not None:
            self.set_field("features", features)    # This can be engine-specific (speaker_id etc.)
        if alternatives is not None:
            self.set_field("alternatives", alternatives)

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
