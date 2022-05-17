"""Module to lauch server with specific settings
More info: https://www.uvicorn.org/deployment/
"""

import sys
import argparse
import uvicorn

from settings import SettingsFile

# Server constants
SERVER_NAME = "SEPIA STT Server"
SERVER_VERSION = "0.10.0"

# Run arguments
argv=sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--settings", action="store",
    help="Settings path", default=None)
ap.add_argument("-p", "--port", action="store",
    help="Server port", default=None)
ap.add_argument("-e", "--engine", action="store",
    help="ASR engine name", default=None)
ap.add_argument("-m", "--model", action="store",
    help="Path of single ASR model relative to base folder", default=None)
ap.add_argument("-r", "--recordings", action="store",
    help="Folder to store recordings, used for example in 'wave_file_writer' engine", default=None)
ap.add_argument("-d", "--log-level", action="store",
    help="Server log level, for example: info, warning", default=None)
ap.add_argument("-c", "--code", action="store_true",
    help="Automatic reload of code changes")
args = ap.parse_args(argv)

# Load settings
settings = SettingsFile(args.settings)
settings.code_reload = args.code    # this is only accessible via command line
if args.port is not None:
    settings.port = int(args.port)
if args.engine is not None:
    settings.asr_engine = args.engine
if args.model is not None:
    settings.asr_model_paths = [args.model]
if args.recordings is not None:
    settings.recordings_path = args.recordings
if args.log_level is not None:
    settings.log_level = args.log_level

def main():
    """Main method to start server"""
    uvicorn.run("server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.code_reload)

def get_settings_response():
    """Get hard-coded settings options for server info message"""
    features = []
    # Vosk features - NOTE: not all of the models support them
    if settings.asr_engine == "vosk":
        features.append("partial_results")
        features.append("alternatives")
        features.append("words_ts")
        features.append("phrase_list")
        if settings.has_speaker_detection_model:
            features.append("speaker_detection")
    # Coqui features
    elif settings.asr_engine == "coqui":
        features.append("partial_results")
        features.append("alternatives")
    # TODO: what about 'dynmaic' ?
    return {
        "version": SERVER_VERSION,
        "engine": settings.asr_engine,
        "models": settings.asr_model_names,
        "languages": settings.asr_model_languages,
        "features": features
        # add more? (e.g. 'engines')
    }

# Run if this is called as main
if __name__ == "__main__":
    main()
else:
    #use Fast API logger here? How? ^^
    print(f"SEPIA STT Server - Settings file used: '{settings.active_settings_file}'")
    print(f"SEPIA STT Server - Settings file tag: '{settings.settings_tag}'")
    print("SEPIA STT Server - Starting...")
