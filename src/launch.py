"""Module to lauch server with specific settings
More info: https://www.uvicorn.org/deployment/
"""

import sys
import argparse
import uvicorn

from settings import SettingsFile

# Server constants
SERVER_NAME = "SEPIA STT Server V2 BETA"
SERVER_VERSION = "0.1.0"

# Run arguments
argv=sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--settings", action="store", help="Settings path", default=None)
ap.add_argument("-p", "--port", action="store", help="Server port", default=None)
ap.add_argument("-c", "--code", action="store_true", help="Automatic reload of code changes")
ap.add_argument("-m", "--model", action="store", help="Path of single ASR model", default=None)
ap.add_argument("-r", "--recordings", action="store", help="Folder for recordings", default=None)
args = ap.parse_args(argv)

# Load settings
settings = SettingsFile(args.settings)
settings.code_reload = args.code    # this is only accessible via command line
if args.port is not None:
    settings.port = int(args.port)
if args.model is not None:
    settings.asr_model_paths = [args.model]
if args.recordings is not None:
    settings.recordings_path = args.recordings

def main():
    """Main method to start server"""
    uvicorn.run("server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.code_reload)

def get_settings_response():
    """Get settings for info messages"""
    features = []
    if settings.has_speaker_detection:
        features.append("speaker_detection")
    if settings.asr_engine == "vosk":
        features.append("partial_results")
    return {
        "version": SERVER_VERSION,
        "engine": settings.asr_engine,
        "models": settings.asr_model_paths,
        "languages": settings.asr_model_languages,
        "features": features
        # add more?
    }

# Run if this is called as main
if __name__ == "__main__":
    main()
else:
    # TODO: how to properly use Fast API logger?
    print(f"SEPIA STT Server - Settings file used: '{settings.active_settings_file}'")
    print(f"SEPIA STT Server - Settings file tag: '{settings.settings_tag}'")
    print("SEPIA STT Server - Starting...")
