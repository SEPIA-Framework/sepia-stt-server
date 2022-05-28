# Changelog for SEPIA Speech-To-Text Server

## v1.0.0 - xx.xx.xxxx

- Added support for Coqui-STT and fully implemented hot-swapping of engines (currently: Vosk + Coqui)
- Added new config file properties for models: 'engine', 'task', 'scorer', 'name'
- Added new config file options for 'asr_engine': 'coqui' and 'dynamic'
- Reworked config file loader to load only ONE file with all settings (no overwrites)
- Added new common 'welcome' message options 'task' and Coqui specific 'hotWords' and 'scorer'
- Accept alias names in 'welcome' message (streamlined with features): 'words_ts', 'phrase_list', 'hot_words' and 'external_scorer'
- Reworked engine interface to load best model depending on: name, full language code (e.g.: de-DE), partial language code (e.g.: de), task or defaults
- Added WebSocket connection heartbeat and timeout to config file
- Improved error handling
- Improved Vosk test script and added Coqui test
- Updated HTML test and demo page

## v0.9.5 - 08.05.2021

- Release of new STT-Server