# SEPIA Speech-To-Text Server

This server supports streaming audio over a WebSocket connection with integration of an open-source ASR decoder like the Kaldi speech recognition toolkit. It can handle full-duplex messaging during the decoding process for intermediate results. The REST interface of the server allows to switch the ASR model on-the-fly.
