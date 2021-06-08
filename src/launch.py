"""Module to lauch server with specific settings
More info: https://www.uvicorn.org/deployment/
"""

import sys
import argparse
import uvicorn

from settings import SettingsFile

# Run arguments
argv=sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--settings", action="store", help="Settings path", default=None)
ap.add_argument("-p", "--port", action="store", help="Server port", default=None)
ap.add_argument("-c", "--code", action="store_true", help="Automatic reload of code changes")
ap.add_argument("-m", "--model", action="store", help="Path of ASR model", default=None)
ap.add_argument("-r", "--recordings", action="store", help="Folder for recordings", default=None)
args = ap.parse_args(argv)

# Load settings
settings = SettingsFile(args.settings)
settings.code_reload = args.code    # this is only accessible via command line
if args.port is not None:
    settings.port = int(args.port)
if args.model is not None:
    settings.asr_model_path = args.model
if args.recordings is not None:
    settings.recordings_path = args.recordings

def main():
    """Main method to start server"""
    uvicorn.run("server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.code_reload)

# Run if this is called as main
if __name__ == "__main__":
    main()
else:
    # TODO: how to properly use Fast API logger?
    print(f"Settings file used: '{settings.active_settings_file}'")
    print(f"Settings file tag: '{settings.settings_tag}'")
    print("Starting server...")
