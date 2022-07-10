"""WebSocket client for SEPIA STT-Server interface"""

import re
import json
import asyncio
import logging
from typing import Callable

import requests

from websockets.client import (WebSocketClientProtocol, connect)
from websockets.exceptions import (ConnectionClosedOK, WebSocketException)
from websockets.connection import State as ConnectionState

logger = logging.getLogger("sepia.stt.client")

class SepiaSttSocketConnectionError(Exception):
    """Error triggered any send failed because connection was not open"""

class SepiaSttSocketMessageError(Exception):
    """Any error triggered during message handling etc."""

class SepiaSttSocketClient:
    """WebSocket client class to handle SEPIA STT-Server connections"""

    def __init__(self,
        server_url: str = "http://localhost:20741",
        client_id: str = "any",
        access_token: str = "test1234",
        engine_options: dict = None,
        server_options: dict = None
    ):
        # Server URLs
        self.server_url = re.sub(r"\/$", "", server_url)
        self.socket_host = re.sub(r"^(http)", "ws", self.server_url) + "/socket"
        logger.debug("STT-Server socket URL: %s", self.socket_host)

        # User auth.
        self.client_id = client_id
        self.access_token = access_token

        # Settings
        self.selected_options = {
			"samplerate": 16000,
			"language": "",
			"task": "",
			"model": "",
            "optimizeFinalResult": True,
            "continuous": True,
            "alternatives": 1
		}
        if engine_options is not None:
            self.selected_options.update(engine_options)

        # Connection and messages
        self._msg_id = 0

        self._websocket: WebSocketClientProtocol = None
        self._is_ready_for_stream = False
        self._result_is_quasi_final = False

        self.auto_close_on_last_final = True
        self._audio_end_submitted = False
        self._skip_auto_welcome = False

        self.onopen: Callable = None
        self.onready: Callable = None
        self.onclose: Callable = None
        self.onresult: Callable = None
        self.onerror: Callable = None
        if server_options is not None:
            if 'onopen' in server_options:
                self.onopen = server_options['onopen']
            if 'onready' in server_options:
                self.onready = server_options['onready']
            if 'onclose' in server_options:
                self.onclose = server_options['onclose']
            if 'onresult' in server_options:
                self.onresult = server_options['onresult']
            if 'onerror' in server_options:
                self.onerror = server_options['onerror']

    # WebSocket Interface:

    def get_message_id(self):
        """Get new message ID"""
        self._msg_id += 1
        if self._msg_id > 999999:
            self._msg_id = 1
        return self._msg_id

    def is_open(self):
        """Is the connection open?"""
        return self._websocket and self._websocket.open

    def is_ready(self):
        """Is the connection ready to send data?"""
        return self.is_open() and self._is_ready_for_stream

    def is_last_result_quasi_final(self):
        """Check if the last received result is final or partial was still empty"""
        return self._result_is_quasi_final
    
    def was_audio_end_submitted(self):
        """Check if audio-end was already sent"""
        return self._audio_end_submitted

    def update_engine_options(self, options: dict):
        """Modify engine options. NOTE: This will only UPDATE fields."""
        self.selected_options.update(options)

    async def _handle_socket_message(self, message):
        """Handle STT-Server messages"""
        msg_json = None
        try:
            # assume JSON
            msg_json = json.loads(message)
        except json.decoder.JSONDecodeError:
            # TODO: handle as error?
            return
        if msg_json and 'type' in msg_json:
            msg_type = msg_json['type']
            logger.debug("Received message of type: %s", msg_type)
            # Error
            if msg_type == "error":
                await self._handle_message_error(msg_json)
            # Ping
            elif msg_type == "ping":
                # Pong
                await self.send_json({"type": "pong", "msg_id": msg_json['msg_id']})
            # Welcome
            elif msg_type == "welcome":
                self._is_ready_for_stream = True
                if self.onready is not None:
                    active_options = (
                        msg_json['info']['options'] if 'info' in msg_json else {})
                    self.onready(active_options)
                    # NOTE: 'active_options' and 'self.selected_options' can be different
            # Result
            elif msg_type == "result":
                is_final = msg_json.get("isFinal", False)
                best_transcript = msg_json.get("transcript", "")
                # some useful states (maybe)
                if is_final or (self._result_is_quasi_final and len(best_transcript) == 0):
                    self._result_is_quasi_final = True
                else:
                    self._result_is_quasi_final = False
                # submit result
                if self.onresult is not None:
                    self.onresult(msg_json)
                # handle result
                if (msg_json.get("isFinal", False) and
                        not self.selected_options.get("continuous", False) and
                        self.auto_close_on_last_final):
                    # after final result, close connection
                    if self._websocket.open:
                        await self._websocket.close()
            # Unknown
            else:
                # TODO: handle?
                pass

    async def _handle_message_error(self, message):
        """Handle STT-Server errors"""
        # Inform and close
        self._is_ready_for_stream = False
        if self._websocket.open:
            await self._websocket.close()
        if self.onerror is not None:
            self.onerror(message)
        else:
            logger.error("Websocket connection error: %s", message)

    async def connect(self):
        """Connect to STT-Server"""

        # reset some stuff
        self._is_ready_for_stream = False
        self._result_is_quasi_final = False
        self._audio_end_submitted = False

        # use async. context manager
        async with connect(self.socket_host) as self._websocket:

            # onopen
            logger.debug("Websocket connection 'onopen'")
            if self.onopen is not None:
                self.onopen()
            if not self._skip_auto_welcome:
                # send welcome
                await self.send_welcome()

            async def handle_socket_messages(websocket: WebSocketClientProtocol):
                """Handle message returned from server"""
                while websocket.state == ConnectionState.OPEN:
                    # alternative syntax: async for message in self._websocket
                    onclosed_pending = True
                    try:
                        # onmessage
                        message = await websocket.recv()
                        logger.debug("Websocket 'onmessage'")
                        await self._handle_socket_message(message)

                    except WebSocketException as err:
                        if isinstance(err, ConnectionClosedOK):
                            # onclose
                            logger.debug("Websocket 'onclose'")
                            if self.onclose is not None:
                                self.onclose()
                            onclosed_pending = False
                        else:
                            # onerror
                            logger.debug("Websocket 'onerror'")
                            await self._handle_message_error(err)
                        # NOTE: we always close on errors
                        break
                # reset some stuff
                self._is_ready_for_stream = False
                if onclosed_pending and self.onclose is not None:
                    self.onclose()  # TODO: should we call or skip this after error?

            await asyncio.wait([
                asyncio.ensure_future(handle_socket_messages(self._websocket))
            ])

    async def close_connection(self):
        """Close connection if open"""
        self._is_ready_for_stream = False
        if self._websocket.open:
            await self._websocket.close()

    async def send_json(self, json_msg: dict):
        """Send a JSON message to server"""
        if self._websocket and self._websocket.open:
            await self._websocket.send(json.dumps(json_msg))
        elif self.onerror:
            self.onerror(SepiaSttSocketConnectionError("not connected"))

    async def send_bytes(self, chunk: bytes):
        """Send a chunk of audio bytes to server for processing"""
        if self._websocket and self._websocket.open:
            #print("send bytes")     # DEBUG
            await self._websocket.send(chunk)
        elif self.onerror:
            self.onerror(SepiaSttSocketConnectionError("not connected"))

    async def send_welcome(self):
        """Send a welcome message to server with recognition options"""
        welcome_msg = {
			"type": "welcome",
			"data": self.selected_options,
			"client_id": self.client_id,
			"access_token": self.access_token,
			"msg_id": self.get_message_id()
		}
        await self.send_json(welcome_msg)

    async def send_audio_end(self, byte_length = None, buffer_or_time_limit = None):
        """Send an audio-end event to server. This will usually finalize the
        transcription and block any further data."""
        if self._audio_end_submitted:
            if self.onerror:
                self.onerror(SepiaSttSocketMessageError("audio-end event already sent"))
            else:
                logger.error("Skipped 'send_audio_end' because it was already sent.")
        else:
            audio_end_msg = {
                "type": "audioend",
                "data": {
                    "byteLength": byte_length,
                    "bufferOrTimeLimit": buffer_or_time_limit
                },
                "msg_id": self.get_message_id()
            }
            await self.send_json(audio_end_msg)
            self._audio_end_submitted = True

    # HTTP Interface:

    def ping_server(self):
        """Ping server to see if connection works and server is online"""
        res = requests.get(self.server_url + "/ping")
        return res.json()

    def load_server_info(self):
        """Get STT-Server info like version and available engines/models"""
        res = requests.get(self.server_url + "/settings")
        return res.json()
