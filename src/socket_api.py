"""Module to handle WebSocket connections and messages"""

import json
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

class SocketJsonMessage(BaseModel):
    """Socket message in JSON format"""
    type: str
    data: dict
    access_token: str
    client_id: str
    msg_id: int
    #{"type": "welcome", "data": { "language": "en-US", "model": "...", "grammar": "..." }, "access_token": "", "client_id": "", "ts": 1620804751062, "msg_id": 1 }

class SocketErrorMessage():
    """Socket error message"""
    def __init__(self, name, message):
        self.json_obj = {"type": "error", "name": name, "message": message}

    def to_string(self):
        """Get error message as JSON string"""
        return json.dumps(self.json_obj)

class SocketManager:
    """Manages WebSocket sessions"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def onopen(self, websocket: WebSocket):
        """WebSocket onopen event"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def on_json_message(self, socket_message: SocketJsonMessage, websocket):
        """Handle messages in JSON format"""
        await websocket.send_text(f"You wrote: {socket_message.data}")

    async def on_binary_message(self, binary_data: bytes, websocket):
        """Handle binary data"""
        print(binary_data)
        await websocket.send_text("You sent bytes")
        # TODO: use 'run_in_threadpool' from 'starlette.concurrency' ?

    def onclose(self, websocket: WebSocket):
        """WebSocket onclose event"""
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        """Send a direct message to a single socket client"""
        await websocket.send_text(message)

    async def broadcast_to_all(self, message: str):
        """Broadcast a message to all connected users"""
        for connection in self.active_connections:
            await connection.send_text(message)

class WebsocketApiEndpoint:
    """Class to handles WebSocket API requests"""
    def __init__(self):
        self.socket_manager = SocketManager()

    async def handle(self, websocket: WebSocket):
        """Handle WebSocket events"""
        await self.socket_manager.onopen(websocket)
        try:
            while True:
                data = await websocket.receive()
                if "text" in data:
                    # JSON messages
                    try:
                        json_obj = SocketJsonMessage.parse_raw(data['text'])
                        await self.socket_manager.on_json_message(json_obj, websocket)
                    except ValidationError:
                        await self.socket_manager.send_message(SocketErrorMessage(
                            "InvalidMessage", "JSON message invalid or incomplete.").to_string(),
                            websocket)
                elif "bytes" in data:
                    # Binary messages
                    await self.socket_manager.on_binary_message(data['bytes'], websocket)
                else:
                    pass

        except WebSocketDisconnect:
            self.socket_manager.onclose(websocket)
            #await socket_manager.broadcast_to_all(f"Client #{client_id} left the chat")
