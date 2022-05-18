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
            print(f"-----Settings INIT: {self.settings_tag}") # TODO: why is this called 2nd time at import ???
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
            self.asr_model_names = []  # build from path + optional (task|scorer) to distinguish
            # Load all model parameters for each model 1...N and filter by engine
            model_index = 1
            num_section_items = len(settings.items("asr_models"))
            current_path = ""
            current_lang = ""
            current_name = ""
            current_params = {}
            for key, val in settings.items("asr_models"):
                num_section_items = num_section_items-1
                if key == "base_folder":
                    # this should have been in a different section ^^
                    continue
                # next index and current collect
                if str(model_index) not in key:
                    model_index += 1
                    self.collect_model(current_path, current_lang, current_name, current_params)
                    current_path = ""
                    current_lang = ""
                    current_name = ""
                    current_params = {}
                # get current
                if val is None or val == "":
                    pass
                elif key == f"path{model_index}":
                    current_path = val
                elif key == f"lang{model_index}":
                    current_lang = val
                elif key == f"name{model_index}":
                    current_name = val
                elif str(model_index) in key:
                    param = key.rsplit(str(model_index), 1)[0]
                    current_params[param] = val
                # collect final
                if num_section_items == 0 or str(model_index) not in key:
                    self.collect_model(current_path, current_lang, current_name, current_params)
            # Speaker models
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

    def collect_model(self, path, lang, name, params: dict):
        """Check if model fits to engine settings and add to collection"""
        # add all models that have no engine parameter or one that fits
        if (self.asr_engine == "dynamic" or "engine" not in params
            or self.asr_engine == params["engine"]):
            # build name for model from name/task/scorer/path
            if name:
                self.asr_model_names.append(name)
            elif "task" in params:
                self.asr_model_names.append("{}:{}".format(
                    path, params["task"]))
            elif "scorer" in params:
                self.asr_model_names.append("{}:{}".format(
                    path, os.path.splitext(params["scorer"])[0]))
            else:
                self.asr_model_names.append(path)
            self.asr_model_paths.append(path)
            self.asr_model_languages.append(lang)
            self.asr_model_properties.append(params)
            #print(f"ASR model added: {path}") # DEBUG
