# Changelog for SEPIA Speech-To-Text Server

## v0.10.0 - xx.xx.xxxx

- Added support for Coqui-STT and allow hot-swap between all engines (Vosk + Coqui)
- Added new settings properties for models: 'engine', 'task', 'scorer', 'name'
- Added new settings options for 'asr_engine': 'coqui' and 'dynamic'
- Reworked settings loader to load only ONE file with all settings (no overwrites)
- Reworked engine interface to load best model depending on: name, full language code (de-DE), partial language code (de), defaults
- Improved Vosk test script and added Coqui test
- Updated HTML test and demo page

## v0.9.5 - 08.05.2021

- Release of new STT-Server