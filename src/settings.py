"""Server settings loader and handling"""

import sys
import os
import configparser

# ordered from low prio to high prio
SETTINGS_PATHS = [
    "./server.conf",
    os.path.expanduser("~") + "/.sepia-stt-server.conf"
]

class SettingsFile:
    """File handler for server settings (e.g. server.conf)"""
    def __init__(self, file_path):
        settings_paths = list(SETTINGS_PATHS)
        if file_path is not None:
            settings_paths = SETTINGS_PATHS + [file_path]

        settings = configparser.ConfigParser()
        if not settings.read(settings_paths):
            print(
                "No settings file found at the following locations: "
                + "".join('\n    {}'.format(sp) for sp in settings_paths),
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate config:
        try:
            self.recordings_path = settings.get("app", "recordings_path")
            self.asr_model_path = settings.get("app", "asr_model_path")
        except configparser.Error as err:
            print("Settings error:", err, file=sys.stderr)
            sys.exit(1)
