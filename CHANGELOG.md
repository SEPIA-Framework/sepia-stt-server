# Changelog for SEPIA Speech-To-Text Server

## v1.0.0 - xx.xx.xxxx

- Added support for Coqui-STT and fully implemented hot-swapping of engines (currently: Vosk + Coqui)
- Added new config file properties for models: 'engine', 'task', 'scorer', 'name'
- Added new config file options for 'asr_engine': 'coqui' and 'dynamic'
- Reworked config file loader to load only ONE file with all settings (no overwrites)
- Reworked engine interface to load best model depending on: name, full language code (de-DE), partial language code (de), defaults
- Added WebSocket connection heartbeat and timeout to config file
- Improved error handling
- Improved Vosk test script and added Coqui test
- Updated HTML test and demo page

## v0.9.5 - 08.05.2021

- Release of new STT-Server