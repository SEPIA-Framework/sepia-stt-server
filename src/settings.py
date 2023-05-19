"""Server settings loader and handling"""

import os
import sys
import re
import configparser

# Server constants
SERVER_NAME = "SEPIA STT Server"
SERVER_VERSION = "1.1.0"

# ordered from hight to low prio
SETTINGS_PATHS = [
    os.path.expanduser("~") + "/.sepia-stt-server.conf",
    "./server.conf"
]

class SettingsError(Exception):
    """Exception for invalid settings or parser errors."""

class SettingsFile:
    """File handler for server settings (e.g. server.conf)"""
    def __init__(self, file_path = None):
        # TODO: consider replacing with YAML or JSON
        # Read ONE single "best" settings file
        settings = configparser.ConfigParser()
        env_settings_path = os.getenv("SEPIA_STT_SETTINGS")
        path_checked = ""
        if file_path is not None:
            # Highest priority: commandline argument
            path_checked = file_path
            settings_read = settings.read(file_path)
        elif env_settings_path is not None:
            # 2nd highest priority: ENV
            path_checked = env_settings_path
            settings_read = settings.read(env_settings_path)
        else:
            # Check rest
            for settings_file in SETTINGS_PATHS:
                path_checked += f"\n  {settings_file}"
                if os.path.exists(settings_file):
                    settings_read = settings.read(settings_file)
                    break
        if not settings_read:
            print("No settings file found at: " + path_checked, file=sys.stderr)
            sys.exit(1)

        # We only read ONE file so this is our active file
        self.active_settings_file = settings_read[0]

        # Validate config:
        try:
            self.settings_tag = settings.get("info", "settings_tag")
            # Server
            self.host = settings.get("server", "host")
            self.port = int(settings.get("server", "port"))
            self.cors_origins = settings.get("server", "cors_origins").split(",")
            self.log_level = settings.get("server", "log_level", fallback="warning")
            #if self.log_level == "warning" or self.log_level == "error":
                # TODO: add specific logger settings
            self.socket_heartbeat_s = int(settings.get(
                "server", "socket_heartbeat_s", fallback="10"))
            self.socket_timeout_s = int(settings.get(
                "server", "socket_timeout_s", fallback="15"))
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
            if self.asr_engine == "all":
                self.asr_engine = "dynamic" # alias for 'dynamic'
            self.hot_swap_engines = (self.asr_engine == "dynamic")
            self.available_engines = set({})   # keep track of all 'dynamic' engines in a set
            self.asr_model_paths = []       # required: folder
            self.asr_model_languages = []   # required: language code 'ab-CD'
            self.asr_model_properties = []  # optional: engine, scorer, tasks, ...
            self.asr_models_folder = settings.get("asr_models", "base_folder")
            self.asr_model_names = []  # build from path + optional (task|scorer) to distinguish
            # Engine-specific settings
            # -- Whisper:
            self.whisper_model_cache_size = int(
                settings.get("whisper", "model_cache_size", fallback="2"))
            self.whisper_cache_expire_time_s = int(
                settings.get("whisper", "cache_expire_time_s", fallback="120"))
            self.whisper_threads_per_model = int(
                settings.get("whisper", "threads_per_model", fallback="2"))
            # Load all model parameters for each model 1...N and filter by engine
            num_section_items = len(settings.items("asr_models"))
            model_index = 1
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
                base_key = re.split(r"\d+", key, 1)[0]
                if key != f"{base_key}{model_index}":
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
                elif key == f"engine{model_index}":
                    if val == "dynamic":
                        # prevent recursion when loading chunk processor
                        raise SettingsError("'engine=dynamic' is NOT ALLOWED as model property!")
                    else:
                        self.available_engines.add(val)
                        current_params["engine"] = val
                elif key == f"{base_key}{model_index}":
                    current_params[base_key] = val
                # collect final
                if num_section_items == 0:
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
        # if engine is not specific we require an 'engine' property
        if self.asr_engine == "dynamic" and "engine" not in params:
            # we need that info
            pass
        # else we add all models that have no engine parameter or one that fits
        elif (self.asr_engine == "dynamic" or
            "engine" not in params or self.asr_engine == params["engine"]):
            # build name for model from name/task/scorer/path
            if name:
                self.asr_model_names.append(name)
            elif "task" in params:
                self.asr_model_names.append(f"{path}:{params['task']}")
            elif "scorer" in params:
                scorer_name = os.path.splitext(params['scorer'])[0]
                self.asr_model_names.append(f"{path}:{scorer_name}")
            else:
                self.asr_model_names.append(path)
            self.asr_model_paths.append(path)
            self.asr_model_languages.append(lang)
            self.asr_model_properties.append(params)
            #print(f"ASR model added: {path}") # DEBUG

    def _get_vosk_features(self):
        """Features available for Vosk engine"""
        features = {"partial_results", "alternatives", "words_ts"}
        features.add("phrase_list")
        if self.has_speaker_detection_model:
            features.add("speaker_detection")
        # NOTE: typically used aliases: "words", "phrases", "speaker"
        return features

    def _get_coqui_features(self):
        """Features available for Coqui engine"""
        features = {"partial_results", "alternatives", "words_ts"}
        features.add("hot_words")
        features.add("external_scorer")
        # NOTE: typically used aliases: "words", "hotWords", "scorer"
        return features

    def _get_whisper_features(self):
        """Features available for Whisper engine"""
        features = {"words_ts"}
        features.add("beamsize")
        features.add("init_prompt")
        features.add("translate")
        # NOTE: typically used aliases: "words", "prompt"
        return features

    def get_settings_response(self):
        """Get (partially hard-coded) settings options for server info message"""
        features = set({})
        # Vosk features
        if self.asr_engine == "vosk":
            features.update(self._get_vosk_features())
        # Coqui features
        elif self.asr_engine == "coqui":
            features.update(self._get_coqui_features())
        # Whisper features
        elif self.asr_engine == "whisper":
            features.update(self._get_whisper_features())
        # Dynamic features
        elif self.asr_engine == "dynamic":
            # use dict instead
            features = {
                "basic": "engine_hot_swap"
            }
            if "vosk" in self.available_engines:
                features["vosk"] = list(self._get_vosk_features())
            if "coqui" in self.available_engines:
                features["coqui"] = list(self._get_coqui_features())
            if "whisper" in self.available_engines:
                features["whisper"] = list(self._get_whisper_features())
            # NOTE: individual engine features should be checked via welcome event
        # Debugging
        elif self.asr_engine == "wave_file_writer":
            features.add("write_file")
            features.add("debug")
        elif self.asr_engine == "test":
            features.add("debug")
        return {
            "version": SERVER_VERSION,
            "engine": self.asr_engine,
            "models": self.asr_model_names,
            "languages": self.asr_model_languages,
            "modelProperties": self.asr_model_properties,
            "features": list(features) if isinstance(features, set) else features
        }
