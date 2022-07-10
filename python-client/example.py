"""Test WebSocket connection to SEPIA STT-Server"""

import sys
import argparse
import asyncio
import logging
from pynput.keyboard import Key, Listener as KeyListener

from microphone import MicrophoneStream
from socket_client import (
    SepiaSttSocketClient, SepiaSttSocketConnectionError, SepiaSttSocketMessageError)

# Logger
logging.getLogger("sepia.stt.client").setLevel(level=logging.WARNING)
logging.getLogger("sepia.stt.microphone").setLevel(level=logging.WARNING)
logger = logging.getLogger("test")
logger.setLevel(level=logging.INFO)

logger.info("?NEVER")   # TODO: message is never shown!
logging.info("SEEN?")   # TODO: required to "fix" logger - WHY??
logger.info("\nWelcome to the SEPIA STT-Server Python client example")   # ... now it works O_o

# Parse arguments
argv=sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server", action="store",
    help="Server URL", default="http://localhost:20741")
ap.add_argument("-l", "--language", action="store",
    help="Language code, e.g.: 'de' or 'en-US'", default="en-US")
ap.add_argument("-t", "--task", action="store",
    help="Model task as seen in welcome message", default="")
ap.add_argument("-m", "--model", action="store",
    help="Model name as seen in welcome message (overwrites lang. and task)", default="")
args = ap.parse_args(argv)

# Server and user defaults
SERVER_URL = args.server if not None else "http://localhost:20741"
CLIENT_ID = "any"           # default STT server user
ACCESS_TOKEN = "test1234"   # default token for user
CONTINUOUS_STT = False      # continue after (a) final result or close
ENGINE_OPTIONS = {
    "language": args.language,  # use short or long code (de, en-US)
    "task": args.task,
    "model": args.model,        # NOTE: overwrites language and task
    # ... there are many more options, see docs or web-demo ...
    "continuous": CONTINUOUS_STT
}

# Client behavior
DISCONNECT_AFTER_RES_IF_MIC_OFF = True   # abort 'continuous' mode if res is quasi-final and mic off
USE_KEYBOARD_CTRL = True    # hold 'r' to start recording, release it to stop
REC_TIME = 8.0              # if keyboard control is off use timer
CHUNK_SIZE = 2048           # microphone chunk size (2048 ~= 128ms at 16khz)

event_loop = asyncio.get_event_loop()   # required to sync mic, key and coroutine threads
audio_queue = asyncio.Queue()

# Set up microphone:

async def audio_queue_handler():
    """Send audio from queue when new data arrives"""
    while True:
        try:
            logger.debug("Waiting for data in audio queue ...")
            data = await audio_queue.get()
            await sepia_stt_client.send_bytes(data)
            # send end signal? (optional but requests final resutl)
            if should_send_audio_end():
                logger.info("Send audio end signal")
                await sepia_stt_client.send_audio_end()
        except (SepiaSttSocketConnectionError, SepiaSttSocketMessageError, TypeError) as err:
            print(f'Error in audio queue: {err}')
            break

async def timed_mic_control():
    """Stop recorder after specific time"""
    await asyncio.sleep(REC_TIME)
    if mic_stream.is_active():
        print("RECORDING stop")
        mic_stream.stop()
        # NOTE: 'disconnect_if_mic_off_and_final_res' will close connection

# Microphone stream (with default settings: Int16, 16khz, mono)
mic_stream = MicrophoneStream(chunk_size=CHUNK_SIZE)
mic_stream.open(audio_queue, event_loop)

def load_keyboard_controls_thread():
    """Keyboard control for microphone"""
    def on_press(key):
        if hasattr(key, 'char'):
            # start recording
            if key.char == "r":
                logger.debug("Pressed 'r'")
                if not mic_stream.is_active():
                    print("RECORDING start")
                    mic_stream.start()
    def on_release(key):
        if hasattr(key, 'char'):
            # stop recording
            if key.char == "r":
                logger.debug("Released 'r'")
                if mic_stream.is_active():
                    print("RECORDING stop")
                    mic_stream.stop()
                    if should_auto_disconnect():
                        asyncio.run_coroutine_threadsafe(
                            disconnect(), event_loop)
                    elif should_send_audio_end():
                        asyncio.run_coroutine_threadsafe(
                            sepia_stt_client.send_audio_end(), event_loop)
        # disconnect
        if key == Key.esc:
            print("Requested ABORT (ESC)")
            asyncio.run_coroutine_threadsafe(disconnect(), event_loop)
            return False
    # Start key-listener thread
    listener = KeyListener(on_press=on_press, on_release=on_release)
    listener.start()    # NOTE: do we need a join somewhere to clean-up?

# Connect to server:

def on_open():
    """Connection open callback"""
    print("\nSTT-Server connection is: OPEN")

def on_ready(active_options: dict):
    """Connection ready callback"""
    print("\nSTT-Server connection is: READY")
    print(f"Active options: {active_options}")
    # start recording and stop after specific time
    if USE_KEYBOARD_CTRL:
        print("\nPress and hold 'r' to start recording, release it to stop. Abort with ESC.")
    else:
        mic_stream.start()
        event_loop.create_task(timed_mic_control())
        print(f"\nRECORDER open for: {REC_TIME}s")

def on_result(result_json: dict):
    """Server result callback with transcription"""
    is_final = result_json.get("isFinal", False)
    best_transcript = result_json.get("transcript", "")
    #print(f"Res: {result_json}")
    if is_final or len(best_transcript) > 0:
        print(f"STT-Server {'FINAL' if is_final else 'partial'} result: {best_transcript}\n")
    if should_auto_disconnect():
        asyncio.ensure_future(disconnect())

def on_close():
    """Connection close callback"""
    print("\nSTT-Server connection is: CLOSED")

def on_error(err):
    """Connection error callback"""
    print(f"\nSTT-Server connection ERROR: {err}")

server_options = {
    "onopen": on_open,
    "onready": on_ready,
    "onresult": on_result,
    "onclose": on_close,
    "onerror": on_error
}
sepia_stt_client = SepiaSttSocketClient(
    server_url = SERVER_URL,
    client_id = CLIENT_ID,
    access_token = ACCESS_TOKEN,
    engine_options = ENGINE_OPTIONS,
    server_options = server_options
)

async def connect():
    """Open SEPIA STT-Server connection"""
    # Load some server data and check connection
    print(f"\nPing server: {sepia_stt_client.ping_server()}")
    server_info = sepia_stt_client.load_server_info()
    print(f"\nServer info: {server_info}")

    # Establish WebSocket connection
    await sepia_stt_client.connect()

async def disconnect():
    """Disconnect if still connected (or ignore)"""
    if sepia_stt_client.is_open():
        logger.info("Closing connection")
        await sepia_stt_client.close_connection()

def should_auto_disconnect():
    """If flag is enabled check if stream is done and should disconnect"""
    if DISCONNECT_AFTER_RES_IF_MIC_OFF and sepia_stt_client.is_last_result_quasi_final():
        if mic_stream.is_stopped() and audio_queue.empty():
            return True
    return False

def should_send_audio_end():
    """Check if audio-end event should be sent"""
    if (not CONTINUOUS_STT and mic_stream.is_stopped() and audio_queue.empty() and
            not sepia_stt_client.was_audio_end_submitted()):
        return True
    return False

# MAIN
def main():
    """Run test"""
    # Control microphone via key listeners
    if USE_KEYBOARD_CTRL:
        load_keyboard_controls_thread()

    # Prepare audio queue
    audio_queue_cr = event_loop.create_task(audio_queue_handler())

    # Connect to server and handle audio
    event_loop.run_until_complete(connect())
    audio_queue_cr.cancel()
    mic_stream.close()

# Run
if __name__ == '__main__':
    main()
