"""Module to process audio chunks sent via socket connection with different methods"""

import time
from functools import partial
from starlette.concurrency import run_in_threadpool

from launch import settings

class ChunkProcessor():
    """Common class to handle byte chunks using different processors"""
    def __init__(self, processor_name = None):
        """Define processor via name"""
        if processor_name is None:
            processor_name = settings.asr_engine
        if processor_name == "wave_writer" or processor_name == "default":
            # Write to file
            self.processor = WaveFileWriter()

    async def process(self, chunk: bytes):
        """Process chunks with given processor"""
        await self.processor.process(chunk)

    async def close(self):
        """Close processor (to clean up and open streams etc.)"""
        await self.processor.close()

#--- FILE WRITER ---

class WaveFileWriter():
    """Write raw PCM audio chunks to wave file"""

    # Static file counter
    file_index = 0

    def __init__(self):
        """Create wave file writer"""
        WaveFileWriter.file_index = WaveFileWriter.file_index + 1
        if WaveFileWriter.file_index > 99:
            WaveFileWriter.file_index = 1
        self.file = open(f"{settings.recordings_path}{WaveFileWriter.file_index}-{int(time.time())}.wav", 'wb')

    async def process(self, chunk: bytes):
        """Write chunks to file"""
        self.file.write(chunk)

    async def close(self):
        """Close file"""
        self.file.close()

#--- TEST ---

class HeavyCompute():
    """Test: https://bocadilloproject.github.io/guide/async.html#converting-a-regular-function-to-an-asynchronous-function"""
    def __init__(self):
        """Create test"""
        self.compute_async = partial(run_in_threadpool, self._compute)
    
    def _compute(self, chunk):
        """Test compute function"""
        time.sleep(5)
        return {"result": "ok"}

    async def process(self, chunk: bytes):
        """Pretend compute"""
        self.compute_async(chunk)

    async def close(self):
        """Nothing?"""
        pass