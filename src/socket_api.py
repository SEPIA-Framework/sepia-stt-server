"""Module to handle WebSocket connections and messages"""

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from pydantic import ValidationError

from socket_messages import (SocketJsonInputMessage, SocketMessage,
    SocketWelcomeMessage, SocketBroadcastMessage, SocketErrorMessage)
from users import SocketUser

class SocketManager:
    """Manages WebSocket sessions"""
    def __init__(self):
        self.active_connections = {}

    async def onopen(self, user: SocketUser):
        """WebSocket onopen event"""
        await user.socket.accept()
        self.active_connections[user.session_id] = user
        # tell all clients that user connected
        #await self.broadcast_to_all(SocketBroadcastMessage(
        #    "chat", {"text": (f"User '{user.session_id}' connected")}))

    async def onclose(self, user: SocketUser):
        """WebSocket onclose event"""
        if self.active_connections[user.session_id] is not None:
            del self.active_connections[user.session_id]
        # tell all clients that user left
        #await self.broadcast_to_all(SocketBroadcastMessage(
        #    "chat", {"text": (f"User '{user.session_id}' left")}))
        await user.on_closed()
        #print("CLIENT CLOSED")

    async def broadcast_to_all(self, message: SocketMessage):
        """Broadcast a message to all connected users"""
        for s_id in self.active_connections:
            await self.active_connections[s_id].send_message(message)

class WebsocketApiEndpoint:
    """Class to handles WebSocket API requests"""
    def __init__(self):
        WebsocketApiEndpoint.socket_manager = SocketManager()

    async def handle(self, websocket: WebSocket):
        """Handle WebSocket events"""
        try:
            user = SocketUser(websocket)
            await WebsocketApiEndpoint.socket_manager.onopen(user)
            # Main WS Loop
            while websocket.client_state == WebSocketState.CONNECTED:
                #if websocket.application_state == WebSocketState.DISCONNECTED
                data = await websocket.receive()
                if "text" in data:
                    # JSON messages
                    try:
                        json_obj = SocketJsonInputMessage.parse_raw(data['text'])
                        await on_json_message(json_obj, user)
                    except ValidationError:
                        await user.send_message(SocketErrorMessage(400,
                            "InvalidMessage", "JSON message invalid or incomplete."))
                elif "bytes" in data:
                    # Binary messages
                    if user.is_authenticated:
                        await on_binary_message(data['bytes'], user)
                    else:
                        await user.send_message(SocketErrorMessage(401,
                            "Unauthorized", "Binary data can only be sent after authentication."))
            # regular disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)
        except WebSocketDisconnect:
            # acceptable disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)
        except RuntimeError:
            # broken disconnect
            await WebsocketApiEndpoint.socket_manager.onclose(user)

# Message handlers:

async def on_json_message(socket_message: SocketJsonInputMessage, user: SocketUser):
    """Handle messages in JSON format"""
    #
    # NOTE: we could implement support for Twilio style message format (binary over JSON object):
    # https://www.twilio.com/docs/voice/tutorials/consume-real-time-media-stream-using-websockets-python-and-flask#

    # handle welcome event
    if socket_message.type == "welcome":
        # Note that client was active
        user.on_client_activity(True)

        if user.is_authenticated and user.processor:
            # User was already auth. and processor was created - for safety we block this atm
            await user.send_message(SocketErrorMessage(418,
                "NotPossible", "Multiple 'welcome' messages in one session are not supported."))
            return

        await user.authenticate(socket_message)
        if not user.processor:
            await user.send_message(SocketErrorMessage(500,
                "Error", "ChunkProcessorError failed to load."))
            await user.socket.close(1000)
        elif user.is_authenticated:
            welcome_message = SocketWelcomeMessage(
                socket_message.msg_id, user.processor.get_options())
            await user.send_message(welcome_message)
        else:
            await user.send_message(SocketErrorMessage(401,
                "Unauthorized", "Authentication failed."))
            await user.socket.close(1000)
            #WebsocketApiEndpoint.socket_manager.onclose(user) # use?

    # handle any authenticated request
    elif user.is_authenticated:
        # Pong
        if socket_message.type == "pong":
            # Note that client was active (but without data)
            user.on_client_activity(False)
        # Audio input end
        elif socket_message.type == "audioend":
            await user.finish_processing(socket_message)
        # Anything else ...
        else:
            # TODO: replace? remove?
            await user.send_message(SocketBroadcastMessage(
                "chat", {"text": (f"You wrote: {socket_message.data}")}))

    # refuse everything else
    else:
        await user.send_message(SocketErrorMessage(401,
            "Unauthorized", "In current state only 'welcome' message is allowed."))

async def on_binary_message(binary_data: bytes, user: SocketUser):
    """Handle binary data (requires authenticated client)"""

    # Note that client was active
    user.on_client_activity(True)

    # Process
    await user.process_audio_chunks(binary_data)
