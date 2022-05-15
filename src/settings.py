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
        settings_paths = list(SETTINGS_PATHS)
        env_settings_path = os.getenv("SEPIA_STT_SETTINGS")
        if env_settings_path is not None:
            # add ENV settings path with high priority
            settings_paths.append(env_settings_path)
        if file_path is not None:
            # add file_path (launch argument) with highest priority
            settings_paths.append(file_path)
        settings = configparser.ConfigParser()
        settings_read = settings.read(settings_paths)
        if not settings_read:
            print(
                "No settings file found at the following locations: "
                + "".join('\n    {}'.format(sp) for sp in settings_paths),
                file=sys.stderr,
            )
            sys.exit(1)

        # The last "readable" file always overwrites all settings
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
            self.asr_engine = settings.get("app", "asr_engine", fallback="dynamic")
            self.asr_model_paths = []       # required: folder
            self.asr_model_languages = []   # required: language code 'ab-CD'
            self.asr_model_properties = []  # optional: engine, scorer, tasks, ...
            self.asr_models_folder = settings.get("asr_models", "base_folder")
            # Load all model parameters for each model 1...N and filter by engine
            model_index = 1
            current_path = ""
            current_lang = ""
            current_params = {}
            for key, val in settings.items("asr_models"):
                if model_index not in key:
                    model_index += 1
                    if self.asr_engine == "dynamic" or not current_params["engine"] or self.asr_engine == current_params["engine"]:
                        self.asr_model_paths.append(current_path)
                        self.asr_model_languages.append(current_lang)
                        self.asr_model_properties.append(current_params)
                    current_path = ""
                    current_lang = ""
                    current_params = {}
                param = key.rsplit(model_index, 1)[0]
                if key == "path":
                    current_path = val
                elif key == "lang":
                    current_lang = val
                else:
                    current_params[param] = val
            self.speaker_model_paths = []
            self.speaker_models_folder = settings.get("speaker_models", "base_folder")
            for key, val in settings.items("speaker_models"):
                if key.startswith("path"):
                    self.speaker_model_paths.append(val)
            if len(self.speaker_model_paths) > 0:
                self.has_speaker_detection_model = True
            else:
                self.has_speaker_detection_model = False
                self.speaker_model_paths.append(None)

        except configparser.Error as err:
            print("Settings error:", err, file=sys.stderr)
            sys.exit(1)
