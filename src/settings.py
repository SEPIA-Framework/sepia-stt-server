"""Server settings loader and handling"""

import os
import sys
import configparser

# ordered from low prio to high prio
SETTINGS_PATHS = [
    "./server.conf",
    os.path.expanduser("~") + "/.sepia-stt-server.conf"
]

class SettingsFile:
    """File handler for server settings (e.g. server.conf)"""
    def __init__(self, file_path):
        env_settings_path = os.getenv("SEPIA_STT_SETTINGS")
        if env_settings_path is not None:
            settings_paths = SETTINGS_PATHS + [env_settings_path]
        settings_paths = list(SETTINGS_PATHS)
        if file_path is not None:
            settings_paths = SETTINGS_PATHS + [file_path]

        settings = configparser.ConfigParser()
        settings_read = settings.read(settings_paths)
        if not settings_read:
            print(
                "No settings file found at the following locations: "
                + "".join('\n    {}'.format(sp) for sp in settings_paths),
                file=sys.stderr,
            )
            sys.exit(1)

        # We assume the last file always overwrites all settings
        self.active_settings_file = settings_read[-1]

        # Validate config:
        try:
            self.settings_tag = settings.get("info", "settings_tag")
            # Server
            self.host = settings.get("server", "host")
            self.port = int(settings.get("server", "port"))
            self.cors_origins = settings.get("server", "cors_origins").split(",")
            self.log_level = settings.get("server", "log_level")
            # Auth
            self.common_auth_token = settings.get("users", "common_auth_token")
            self.user_tokens = {}
            last_user = ""
            for key, val in settings.items("users"):
                if key.startswith("user"):
                    last_user = val
                elif key.startswith("token"):
                    self.user_tokens[last_user] = val
            # Engines
            self.recordings_path = settings.get("app", "recordings_path")
            self.asr_engine = settings.get("app", "asr_engine")
            self.asr_model_paths = []
            self.asr_model_languages = []
            for key, val in settings.items("asr_models"):
                if key.startswith("path"):
                    self.asr_model_paths.append(val)
                elif key.startswith("lang"):
                    self.asr_model_languages.append(val)
            self.speaker_model_paths = []
            for key, val in settings.items("speaker_models"):
                if key.startswith("path"):
                    self.speaker_model_paths.append(val)
            if len(self.speaker_model_paths) > 0:
                self.has_speaker_detection = True
            else:
                self.has_speaker_detection = False
                self.speaker_model_paths.append(None)
                
        except configparser.Error as err:
            print("Settings error:", err, file=sys.stderr)
            sys.exit(1)
