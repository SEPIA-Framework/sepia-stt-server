"""Module to handle WebSocket connections and messages"""

from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

class SocketManager:
    """Manages WebSocket sessions"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def onopen(self, websocket: WebSocket):
        """WebSocket onopen event"""
        await websocket.accept()
        self.active_connections.append(websocket)

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

class SocketJsonMessage(BaseModel):
    """Socket message in JSON format"""
    type: str
    access_token: str
    client_id: str
    msg_id: int
    #{"type": "welcome", "data": { "language": "en-US", "model": "...", "grammar": "..." }, "access_token": "", "client_id": "", "ts": 1620804751062, "msg_id": 1 }


class WebsocketApiEndpoint:
    """Class to handles WebSocket API requests"""
    def __init__(self):
        self.socket_manager = SocketManager()

    async def handle(self, websocket: WebSocket):
        """Handle WebSocket events"""
        await self.socket_manager.onopen(websocket)
        try:
            while True:
                # TODO: use 'run_in_threadpool' from 'starlette.concurrency' ?
                data = await websocket.receive()
                print(data)
                if "text" in data:
                    await self.socket_manager.send_message(f"You wrote: {data['text']}", websocket)
                elif "bytes" in data:
                    await self.socket_manager.send_message(f"You sent bytes", websocket)
                #await socket_manager.broadcast_to_all(f"Client #{client_id} says: {data}")

        except WebSocketDisconnect:
            self.socket_manager.onclose(websocket)
            #await socket_manager.broadcast_to_all(f"Client #{client_id} left the chat")
