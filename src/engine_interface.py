"""Chunk processor engine interface"""

from socket_messages import SocketTranscriptMessage, SocketErrorMessage

class EngineInterface():
    """Interface for chunk processor engines"""
    def __init__(self, send_message = None):
        self.send_message = send_message
        self.accept_chunks = True
        self.is_open = True

    async def process(self, chunk: bytes):
        """Process chunk"""
    async def finish_processing(self):
        """Block new process requests, wait for last process to finish and send result"""
    async def close(self):
        """Close and clean up"""

    async def send_transcript(self,
        transcript, is_final = False, confidence = -1, features = None, alternatives = None):
        """Send transcript result"""
        if self.send_message is not None:
            msg = SocketTranscriptMessage(
                transcript, is_final, confidence, features, alternatives)
            await self.send_message(msg)

    async def on_before_close(self):
        """Run before close for any required extra action"""
        self.is_open = False

    async def on_error(self, error_message):
        """Send error message"""
        self.accept_chunks = False
        if self.send_message is not None:
            await self.send_message(
                SocketErrorMessage(500, "AsrEngineError", error_message))