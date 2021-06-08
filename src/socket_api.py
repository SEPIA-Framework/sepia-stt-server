"""Module to handle WebSocket connections and messages"""

from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from pydantic import BaseModel, ValidationError

from authentication import SocketUser
from launch import settings, SERVER_VERSION

class SocketJsonMessage(BaseModel):
    """Incoming socket message in JSON format"""
    type: str   # for example: "welcome"
    data: dict
    access_token: Optional[str] = None
    client_id: Optional[str] = None
    msg_id: int
    #{"type": "welcome", "data": { "language": "en-US", "model": "...", "grammar": "..." }, "access_token": "", "client_id": "", "ts": 1620804751062, "msg_id": 1 }

class SocketMessage():
    """Default socket message"""
    def __init__(self, msg_type):
        self.json = {"type": msg_type, "code": 200}

class SocketBroadcastMessage(SocketMessage):
    """Socket message for broadcast"""
    def __init__(self, msg_type, data):
        super().__init__(msg_type)
        self.json["data"] = data

class SocketErrorMessage(SocketMessage):
    """Socket error message"""
    def __init__(self, code, name, message):
        super().__init__("error")
        self.json["code"] = code
        self.json["name"] = name
        self.json["message"] = message

class SocketManager:
    """Manages WebSocket sessions"""
    def __init__(self):
        self.active_connections = {}

    async def onopen(self, user: SocketUser):
        """WebSocket onopen event"""
        await user.socket.accept()
        self.active_connections[user.session_id] = user
        await self.broadcast_to_all(SocketBroadcastMessage("chat", {"text": (f"User '{user.session_id}' connected")}))

    async def onclose(self, user: SocketUser):
        """WebSocket onclose event"""
        if (self.active_connections[user.session_id] is not None):
            del self.active_connections[user.session_id]
        await self.broadcast_to_all(SocketBroadcastMessage("chat", {"text": (f"User '{user.session_id}' left")}))

    async def broadcast_to_all(self, message: SocketMessage):
        """Broadcast a message to all connected users"""
        for s_id in self.active_connections:
            await self.active_connections[s_id].socket.send_json(message.json)

class WebsocketApiEndpoint:
    """Class to handles WebSocket API requests"""
    def __init__(self):
        WebsocketApiEndpoint.socket_manager = SocketManager()
        
    async def handle(self, websocket: WebSocket):
        """Handle WebSocket events"""
        user = SocketUser(websocket)
        await WebsocketApiEndpoint.socket_manager.onopen(user)
        try:
            while websocket.client_state == WebSocketState.CONNECTED:
                #if websocket.application_state == WebSocketState.DISCONNECTED
                data = await websocket.receive()
                if "text" in data:
                    # JSON messages
                    try:
                        json_obj = SocketJsonMessage.parse_raw(data['text'])
                        await on_json_message(json_obj, user)
                    except ValidationError:
                        await send_message(SocketErrorMessage(400,
                            "InvalidMessage", "JSON message invalid or incomplete."), user)
                elif "bytes" in data:
                    # Binary messages
                    if (user.is_authenticated):
                        await on_binary_message(data['bytes'], user)
                    else:
                        await send_message(SocketErrorMessage(401,
                            "Unauthorized", "Binary data can only be sent after authentication."), user)
            # regular disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)
        except WebSocketDisconnect:
            # acceptable disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)
        except RuntimeError:
            # broken disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)

# Message handlers:

async def on_json_message(socket_message: SocketJsonMessage, user: SocketUser):
    """Handle messages in JSON format"""

    # handle welcome event
    if socket_message.type == "welcome":
        await user.authenticate(socket_message.client_id, socket_message.access_token)
        if user.is_authenticated:
            welcome_message = SocketMessage("welcome")
            welcome_message.json["info"] = {
                "version": SERVER_VERSION,
                "engine": settings.asr_engine,
                "models": settings.asr_model_paths,
                "more": "tbd"
                # add e.g.: languages, engine, models, features...
            }
            welcome_message.json["msg_id"] = socket_message.msg_id
            await send_message(welcome_message, user)
        else:
            await send_message(SocketErrorMessage(401,
                "Unauthorized", "Authentication failed."), user)
            await user.socket.close()
            #WebsocketApiEndpoint.socket_manager.onclose(user) # TODO: use?
    
    # handle any authenticated request
    elif user.is_authenticated:
        await send_message(SocketBroadcastMessage(
            "chat", {"text": (f"You wrote: {socket_message.data}")}), user)
    
    # refuse everything else
    else:
        await send_message(SocketErrorMessage(401,
            "Unauthorized", "In current state only 'welcome' message is allowed."), user)

async def on_binary_message(binary_data: bytes, user: SocketUser):
    """Handle binary data"""
    await user.socket.send_text("You sent bytes")
    # TODO: use 'run_in_threadpool' from 'starlette.concurrency' ?

async def send_message(message: SocketMessage, user: SocketUser):
    """Send a direct message to a single socket client"""
    await user.socket.send_json(message.json)