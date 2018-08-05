#!/usr/bin/env python

from __future__ import absolute_import, print_function

import argparse
import ConfigParser as configparser
import io
import logging
import os
import sys
import time
from ConfigParser import SafeConfigParser as ConfigParser
from logging import debug, info

import tornado.ioloop
import tornado.websocket
import tornado.httpserver
import tornado.template
import tornado.web
# import webrtcvad
from tornado.web import url
import json

#Only used for record function
import datetime
import wave

#Decoder
import struct
import numpy as np
#from time           import time
from kaldiasr.nnet3 import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder

SERVER_VERSION = "0.8.0"

CLIP_MIN_MS = 200  # 200ms - the minimum audio clip that will be used
MAX_LENGTH = 8000  # Max length of a sound clip for processing in ms
SILENCE = 20  # How many continuous frames of silence determine the end of a phrase

# Constants:
BYTES_PER_FRAME = 640  # Bytes in a frame
MS_PER_FRAME = 20  # Duration of a frame in ms

CLIP_MIN_FRAMES = CLIP_MIN_MS // MS_PER_FRAME

# Global variables
connections = {}
processors = {}
decoders = {}

def get_processor(cli):
    return processors["default"]
def set_default_processor(processor):
    processors["default"] = processor
def get_decoder(cli):
    return decoders["default"]
def set_default_decoder(decoder):
    decoders["default"] = decoder

# This should be least-specific -> most-specific:
CONFIG_PATHS = [
    "./app.conf",
    "/app/share/sepia_stt_server/app.conf",
    os.path.expanduser("~") + "/share/sepia_stt_server/app.conf",
]

def run_os_cmd(cmd, work_dir):
    cmd = '/bin/bash -c "pushd %s && bash %s && popd"' % (work_dir, cmd)
    info (cmd)
    os.system (cmd)

class BufferedPipe(object):
    def __init__(self, max_frames):
        """
        Create a buffer which will call the provided processor (sink) when full.

        It will call the processor with the number of frames and the accumulated bytes when it reaches
        `max_buffer_size` frames.
        """
        self.max_frames = max_frames

        self.count = 0
        self.payload = b''

    def append(self, data, cli):
        """ Add another data to the buffer. `data` should be a `bytes` object. """

        self.count += 1
        self.payload += data

        if self.count == self.max_frames:
            self.process(cli)

    def process(self, cli):
        """ Process and clear the buffer. """

        get_processor(cli).process(self.count, self.payload, cli)
        self.count = 0
        self.payload = b''


class Processor(object):
    def __init__(self, config):
        self.recordings_path = config.recordings_path
    def process(self, count, payload, cli):
        if count > CLIP_MIN_FRAMES:  # If the buffer is less than CLIP_MIN_MS, ignore it
            info('Processing {} frames from {}'.format(count, cli))
            file_name = "{}rec-{}-{}.wav".format(self.recordings_path, cli, datetime.datetime.now().strftime("%Y%m%dT%H%M%S"))
            output = wave.open(file_name, 'wb')
            output.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))  # nchannels, sampwidth, framerate, nframes, comptype, compname
            output.writeframes(payload)
            output.close()
            info('File written {}'.format(file_name))
            #------------------------------
            try:
                get_decoder(cli).decode_wav_file(file_name, cli)
            except:
                info("Decoding ERROR of %s" % file_name)
                connections[cli].write_message('eDecoding error')
            #------------------------------
            # conn = connections[cli]
            # conn.write_message('fFinal result, file written')
        else:
            info('Discarding {} frames'.format(str(count)))    
    def playback(self, content, cli):
        frames = len(content) // 640
        info("Playing {} frames to {}".format(frames, cli))
        pos = 0
        for x in range(0, frames + 1):
            newpos = pos + 640
            debug("writing bytes {} to {} to socket for {}".format(pos, newpos, cli))
            data = content[pos:newpos]
            connections[cli].write_message(data, binary=True)
            time.sleep(0.018)
            pos = newpos

class Decoder(object):
    def __init__(self, kaldi_model_path):
        self.model_dir = kaldi_model_path 		#'/opt/kaldi/model/kaldi-generic-en-tdnn_sp'
        
        info("Loading Kalid model %s ...", self.model_dir)
        time_start = time.time()
        self.kaldi_model = KaldiNNet3OnlineModel(self.model_dir, acoustic_scale=1.0, beam=7.0, frame_subsampling_factor=3)
        info("Done, took {}".format(time.time()-time_start))
        
        info('Creating Kalid decoder...')
        time_start = time.time()
        self.decoder = KaldiNNet3OnlineDecoder(self.kaldi_model)
        info("Done, took {}".format(time.time()-time_start))

    def decode_wav_file(self, file_name, cli):
        time_start = time.time()
        if self.decoder.decode_wav_file(file_name):
            s, l = self.decoder.get_decoded_string()
            info("Decoding took %8.2fs, likelyhood: %f" % (time.time() - time_start, l))
            info("Result: " + s)
            connections[cli].write_message('f' + s)
        else:
            info("Decoding of %s failed." % file_name)
            connections[cli].write_message('eDecoding failed')


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({"msg": "Hello world!"})

class ControlsHandler(tornado.web.RequestHandler):
    def check_origin(self, origin):
	    return True

    def get(self):
        self.write({
            "server_version": SERVER_VERSION,
            "model": get_decoder("").model_dir
        })

    def post(self):
        content_type = self.request.headers['Content-Type']
        token = ""
        kaldi_model = ""
        adapt_de = ""
        adapt_en = ""
        if content_type == "application/json":
            try:
                data = tornado.escape.json_decode(self.request.body)
                if "token" in data: token = data["token"]
                if "kaldi_model" in data: kaldi_model = data["kaldi_model"]
                if "adapt_de" in data: adapt_de = data["adapt_de"]
                if "adapt_en" in data: adapt_en = data["adapt_en"]
            except:
                self.write({
                    'error': True, 
                    'msg': 'Missing request body.'
                })
                return    
        else:
            token = self.get_argument('token', '')
            kaldi_model = self.get_argument('kaldi_model', '')
            adapt_de = self.get_argument('adapt_de', '')
            adapt_en = self.get_argument('adapt_en', '')
        if not token:
            self.write({
                'error': True, 
                'msg': 'Please submit an authentication token.'
            })
            return
        else:
            if token != "test":
                self.write({
                    'error': True, 
                    'msg': 'Please submit a valid token.'
                })
                return
            else:
                if kaldi_model:
                    #Set new default decoder
                    old_model = get_decoder("").model_dir
                    try:
                        set_default_decoder(Decoder(kaldi_model))
                        self.write({
                            'success': True, 
                            'msg': 'Set new Kaldi model.',
                            "new": kaldi_model,
                            "old": old_model
                        })
                    except:
                        self.write({
                            'error': True, 
                            'msg': 'Cannot set this Kaldi model! Please check the path again.'
                        })

                elif adapt_de:
                    cmd = "adapt_build_move_de.sh %s" % adapt_de
                    run_os_cmd(cmd, "/app/lm_adapt")
                    self.write({
                        'success': True, 
                        'msg': 'Executed cmd, plz check console for errors.',
                        "cmd": "/app/lm_adapt/adapt_build_move_de.sh %s" % adapt_de
                    })

                elif adapt_en:
                    cmd = "adapt_build_move_en.sh %s" % adapt_en
                    run_os_cmd(cmd, "/app/lm_adapt")
                    self.write({
                        'success': True, 
                        'msg': 'Executed cmd, plz check console for errors.',
                        "cmd": "/app/lm_adapt/adapt_build_move_en.sh %s" % adapt_en
                    })
                    
                else:
                    self.write({
                        'success': True, 
                        'msg': 'All good, but nothing changed.'
                    })
                    
                return

class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
	    return True
		
    def initialize(self):
        # Create a buffer which will call `process` when it is full
        self.frame_buffer = BufferedPipe(MAX_LENGTH // MS_PER_FRAME)
        # Setup the Voice Activity Detector
        self.tick = None
        self.cli = None
        self.frames = None
        # self.vad = webrtcvad.Vad()
        # self.vad.set_mode(1)  # Level of sensitivity
		
    def open(self):
        info("client connected")
        # Add the connection to the list of connections
        self.tick = 0
        self.frames = 0
        # TODO: handle multiple users
        self.cli = "onlyonearound"              # TODO: we currently support only one user
        connections[self.cli] = self
		
    def on_message(self, message):
        # Check if message is Binary or Text
        debug("got message, type: " + type(message).__name__)
        if type(message) == unicode:
            self.write_message('You sent unicode: ' + message)
            info("data: " + message)
        elif type(message) == str:
            # self.write_message('You sent str: ' + message)
            # info("data: " + message)
            self.frames += 1
            debug(" {}".format(self.frames))
            if self.frames == 30:
                self.write_message('iIntermediate result')
            elif self.frames == 60:
                self.write_message('iFinished listening, processing ...')
                self.frame_buffer.append(message, self.cli)
                self.frame_buffer.process(self.cli)
            else:
                self.frame_buffer.append(message, self.cli)
            # if self.vad.is_speech(message, 16000):
                # debug ("SPEECH from {}".format(self.cli))
                # self.tick = SILENCE
                # self.frame_buffer.append(message, self.cli)
            # else:
                # debug("Silence from {} TICK: {}".format(self.cli, self.tick))
                # self.tick -= 1
                # if self.tick == 0:
                    # self.frame_buffer.process(self.cli)  # Force processing and clearing of the buffer
        else:
            info(message)
            # Here we should be extracting the meta data that was sent and attaching it to the connection object
            # data = json.loads(message)
            # self.cli = data['cli']
            # connections[self.cli] = self
            self.write_message('ok')

    def on_close(self):
        # Remove the connection from the list of connections
        del connections[self.cli]
        info("client disconnected")


class Config(object):
    def __init__(self, specified_config_path):
        config_paths = list(CONFIG_PATHS)
        if specified_config_path is not None:
            config_paths = CONFIG_PATHS + [specified_config_path]

        config = ConfigParser()
        if not config.read(config_paths):
            print(
                "No config file found at the following locations: "
                + "".join('\n    {}'.format(cp) for cp in config_paths),
                file=sys.stderr,
            )
            sys.exit(1)
			
        # Validate config:
        try:
            #self.host = config.get("app", "host")
            #self.event_url = "http://{}/event".format(self.host)
            self.config_name = config.get("app", "config_name")
            self.port = config.getint("app", "port")
            self.recordings_path = config.get("app", "recordings_path")
            self.kaldi_model_path = config.get("app", "kaldi_model_path")
        except configparser.Error as e:
            print("Configuration Error:", e, file=sys.stderr)
            sys.exit(1)


def main(argv=sys.argv[1:]):
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("-v", "--verbose", action="count")
        ap.add_argument("-c", "--config", default=None)

        args = ap.parse_args(argv)

        logging.basicConfig(
            level=logging.INFO if args.verbose < 1 else logging.DEBUG,
            format="%(levelname)7s %(message)s",
        )

        #Load config
        config = Config(args.config)
        info("Config name: %s", config.config_name)
		
        #Load decoder
        set_default_decoder(Decoder(config.kaldi_model_path))
                
        #Pass any config for the processor into this argument.
        set_default_processor(Processor(config))

        application = tornado.web.Application([
			url(r'/ping', PingHandler),
            url(r'/settings', ControlsHandler),
            url(r'/socket', WSHandler)
        ])

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(config.port)
        info("Running SEPIA STT-Server on port %s", config.port)
        tornado.ioloop.IOLoop.instance().start()		
    except KeyboardInterrupt:
        pass  # Suppress the stack-trace on quit


if __name__ == "__main__":
    main()
