"""Handle device microphone"""

import asyncio
import logging

import pyaudio

logger = logging.getLogger("sepia.stt.microphone")

class MicrophoneStream:
    """Get byte stream from a microphone"""

    def __init__(self,
        audio_format: int = pyaudio.paInt16,
        samplerate: int = 16000,
        channels: int = 1,
        chunk_size: int = 4096
    ):
        self.format = audio_format
        self.samplerate = samplerate
        self.channels = channels
        self.chunk_size = chunk_size

        self._pyaudio = pyaudio.PyAudio()
        self.stream = None
        self.chunk_queue = None
        self.event_loop = None

    def _stream_data_callback(self, input_data, frame_count, time_info, status):
        """Handle microphone stream data, fill chunk_queue and sync with event_loop thread"""
        logger.debug("Mic status: %s - frames: %s - time: %s", status, frame_count, time_info)
        # run async in correct thread (ignore future?):
        asyncio.run_coroutine_threadsafe(self.chunk_queue.put(input_data), self.event_loop)
        return (input_data, pyaudio.paContinue)

    def open(self, chunk_queue: asyncio.Queue, event_loop: asyncio.AbstractEventLoop):
        """Open new pyaudio stream and return audio via chunk_queue to event_loop thread"""
        self.stream = self._pyaudio.open(
            format = self.format,
            channels = self.channels,
            rate = self.samplerate,
            input = True,
            start = False,  # prevent auto-start
            frames_per_buffer = self.chunk_size,
            stream_callback = self._stream_data_callback
        )
        self.chunk_queue = chunk_queue
        self.event_loop = event_loop
        logger.debug("Pyaudio opened with: %shz, ch.: %s, buffer frames: %s, f: %s",
            self.samplerate, self.channels, self.chunk_size, self.format)

    def start(self):
        """Start stream"""
        logger.debug("Microphone stream start")
        self.stream.start_stream()

    def is_active(self):
        """Is the stream active?"""
        return self.stream.is_active()

    def stop(self):
        """Stop stream"""
        logger.debug("Microphone stream stop")
        self.stream.stop_stream()

    def is_stopped(self):
        """Is the stream stopped?"""
        return self.stream.is_stopped()

    def close(self):
        """Close stream and terminate audio instance"""
        logger.debug("Microphone stream close and terminate")
        self.stream.close()
        self._pyaudio.terminate()
