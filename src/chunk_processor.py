"""Module to process audio chunks sent via socket connection with different methods"""

import time
from functools import partial
from starlette.concurrency import run_in_threadpool
from uvicorn.config import logger

from launch import settings
from socket_messages import (SocketJsonInputMessage, SocketResponseMessage, SocketErrorMessage)
from engine_interface import EngineInterface
from engine_vosk import VoskProcessor

class ChunkProcessor():
    """Common class to handle byte chunks using different processors"""
    def __init__(self, processor_name: str = None, send_message = None, options = None):
        """Define processor via name"""
        self.send_message = send_message
        if processor_name is None:
            processor_name = settings.asr_engine
        # Vosk ASR
        if processor_name == "vosk":
            self.processor = VoskProcessor(send_message, options)
        # Write to file
        elif processor_name == "wave_file_writer":
            self.processor = WaveFileWriter(send_message)
        # Test
        elif processor_name == "test":
            self.processor = ThreadTestProcessor(send_message)

    async def process(self, chunk: bytes):
        """Process chunks with given processor"""
        if self.processor is not None and self.processor.is_open and self.processor.accept_chunks:
            await self.processor.process(chunk)
        else:
            if self.send_message is not None:
                await self.send_message(
                    SocketErrorMessage(400, "ProcessError",
                        "Chunk processor was (already) closed or didn't accept data (anymore)"))

    async def finish_processing(self, message: SocketJsonInputMessage):
        """Stop accepting chunks and wait for last result"""
        if self.processor is not None and self.processor.is_open and self.processor.accept_chunks:
            self.processor.accept_chunks = False
            if self.send_message is not None:
                await self.send_message(SocketResponseMessage(message.msg_id, "audioend"))
            await self.processor.finish_processing()

    async def close(self):
        """Close processor (to clean up and close streams etc.)"""
        if self.processor is not None and self.processor.is_open:
            await self.processor.close()

#--- FILE WRITER ---

class WaveFileWriter(EngineInterface):
    """Write raw PCM audio chunks to wave file. This processor is usually only used for testing."""

    # Static file counter
    file_index = 0

    def __init__(self, send_message):
        """Create wave file writer"""
        super().__init__(send_message)
        try:
            WaveFileWriter.file_index = WaveFileWriter.file_index + 1
            if WaveFileWriter.file_index > 99:
                WaveFileWriter.file_index = 1
            self._file_name = f"{settings.recordings_path}{WaveFileWriter.file_index}-{int(time.time())}.wav"
            self._file = open(self._file_name, 'wb')
            logger.info("WaveFileWriter - Created file: %s", self._file_name)
        except OSError:
            logger.exception("WaveFileWriter - Failed to create file")
            self.on_error("Engine: wave_file_writer - Message: Failed to create file")

    async def process(self, chunk: bytes):
        """Write chunks to file"""
        try:
            self._file.write(chunk)
        except OSError:
            logger.exception("WaveFileWriter - Failed to process")
            self.on_error("Engine: wave_file_writer - Message: Failed to process")

    async def finish_processing(self):
        """Send finish confirm. Since file.write is sync. we should be safe."""
        self._close_file()
        await self.send_transcript("[file closed]", True, 1.0)

    async def close(self):
        """Close file"""
        await self.on_before_close()
        self._close_file()

    def _close_file(self):
        """Try to close file"""
        try:
            if self._file is not None and not self._file.closed:
                self._file.close()
                logger.info("WaveFileWriter - File closed: %s", self._file_name)
        except OSError:
            logger.exception("WaveFileWriter - Failed to close file")
            self.on_error("Engine: wave_file_writer - Message: Failed to close")

#--- TEST ---

class ThreadTestProcessor(EngineInterface):
    """Test: https://bocadilloproject.github.io/guide/async.html#converting-a-regular-function-to-an-asynchronous-function"""
    def __init__(self, send_message):
        """Create test"""
        super().__init__(send_message)
        self.compute_async = partial(run_in_threadpool, self._compute)
        self._total_bytes = 0
        self._is_processing = False

    def _compute(self, chunk: bytes):
        """Test compute function"""
        time.sleep(0.05)
        return len(chunk)

    async def process(self, chunk: bytes):
        """Pretend compute"""
        self._is_processing = True
        add_length = await self.compute_async(chunk)
        self._total_bytes += add_length
        self._is_processing = False
        # End?
        if not self.accept_chunks:
            await self._finish()

    async def finish_processing(self):
        """Wait for last process and end"""
        # End?
        if not self._is_processing:
            await self._finish()

    async def close(self):
        """Nothing?"""
        self.compute_async = None

    async def _finish(self):
        """Send final message"""
        await self.send_transcript(f"[processed bytes: {self._total_bytes}]", True, 1.0)
