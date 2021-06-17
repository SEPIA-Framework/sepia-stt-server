"""Authenticate and handle users"""

import time
import asyncio

from uvicorn.config import logger
from fastapi import WebSocket

from launch import settings
from socket_messages import (SocketJsonInputMessage,
    SocketMessage, SocketPingMessage, SocketErrorMessage)
from chunk_processor import ChunkProcessor

# For now we just use a simple static token.
COMMON_TOKEN = settings.common_auth_token

# Client timeout - kick fast
HEARTBEAT_DELAY = 10
TIMEOUT_SECONDS = 15

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
        self.is_alive = True
        self.last_alive_sign = int(time.time())
        self.socket = websocket
        self.session_id = SessionIds.get_new_sesstion_id()
        self.task = self.create_heartbeat_loop_task()
        self.processor = None

    async def authenticate(self, socket_message: SocketJsonInputMessage):
        """Check if user is valid"""
        client_id = socket_message.client_id
        token = socket_message.access_token
        processor_options = socket_message.data
        # Try one token for all
        if COMMON_TOKEN and token == COMMON_TOKEN:
            self.is_authenticated = True
        # Try user list
        elif client_id and token:
            if client_id in settings.user_tokens:
                user_token = settings.user_tokens[client_id]
                if user_token is not None and user_token == token:
                    self.is_authenticated = True
        # Create processor
        if self.is_authenticated:
            try:
                self.processor = ChunkProcessor(processor_name=None, 
                    send_message=self.send_message, options=processor_options)
            except RuntimeError:
                logger.exception("ChunkProcessor - Failed to create processor")
                await self.send_message(SocketErrorMessage(500,
                    "ChunkProcessorError", "Failed to create processor."))
        else:
            logger.warning("User %s failed to authenticate!", client_id)
            await asyncio.sleep(3)

    async def send_message(self, message: SocketMessage):
        """Send socket message to user"""
        await self.socket.send_json(message.json)

    async def ping_client(self):
        """Send alive ping to client (and expect pong answer)"""
        ping_msg = SocketPingMessage(msg_id = None)
        await self.send_message(ping_msg)

    def on_client_activity(self, is_binary_or_welcome):
        """When message is received set last active time"""
        # NOTE: we count only data messages as life sign (why else would the client stay?)
        if is_binary_or_welcome:
            self.last_alive_sign = int(time.time())
    
    async def on_closed(self):
        """Connection was closed"""
        self.is_alive = False
        # Close processor
        if self.processor is not None:
            await self.processor.close()
            self.processor = None

    async def heartbeat_loop(self):
        """Continous heart-beat check to make sure inactive
        clients are kicked fast"""
        while self.is_alive:
            await asyncio.sleep(HEARTBEAT_DELAY)
            if (int(time.time()) - self.last_alive_sign) > TIMEOUT_SECONDS:
                # We are kind and inform the user that he will be kicked :-p
                await self.send_message(SocketErrorMessage(408,
                    "TimeoutMessage", "Client was inactive for too long."))
                self.is_alive = False
                await self.socket.close(1013)
                #self.task.cancel()
            elif self.is_alive:
                await self.ping_client()

    def create_heartbeat_loop_task(self):
        """Create heart-beat loop task"""
        loop = asyncio.get_running_loop()
        return loop.create_task(self.heartbeat_loop())

    async def process_audio_chunks(self, chunk: bytes):
        """Process audio chunks with given processor"""
        if self.processor is not None:
            await self.processor.process(chunk)

    async def finish_processing(self, message: SocketJsonInputMessage):
        """Stop accepting audio chunks and wait for last  result"""
        if self.processor is not None:
            await self.processor.finish_processing(message)
