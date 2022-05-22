"""Module to initialize lauch and hold setttings"""

import sys
import argparse

from settings import SettingsFile

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
# overwrite some file settings with arguments
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

#use Fast API logger here? How? ^^
print(f"SEPIA STT Server - Settings file used: '{settings.active_settings_file}'")
print(f"SEPIA STT Server - Settings file tag: '{settings.settings_tag}'")
