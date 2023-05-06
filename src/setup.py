"""Setup for SEPIA STT Server"""

import os
from itertools import chain

from setuptools import setup, find_packages


base_dir = os.path.dirname(os.path.abspath(__file__))


# Description
def get_long_description():
    """Load long description from README.md"""
    readme_path = os.path.join(base_dir, os.pardir, "README.md")
    with open(readme_path, encoding="utf-8") as fh:
        return fh.read()


# Read requirements from files
def req_file(filename):
    """Load requirements from txt files."""
    req_file_path = os.path.join(base_dir, filename)
    with open(req_file_path, encoding="utf-8") as fh:
        content = fh.readlines()
    return [x.split("#")[0].strip() for x in content]


install_requires = req_file("requirements_server.txt")
extras_require = {
    # STT engines
    "vosk": req_file("requirements_vosk.txt"),
    "coqui": req_file("requirements_coqui.txt"),
    "whisper": req_file("requirements_whisper.txt"),
}
extras_require["core"] = list(chain([extras_require["vosk"]]))
extras_require["all"] = list(chain(
    [extras_require["vosk"], extras_require["coqui"], extras_require["whisper"]]
))


setup(
    name="sepia-stt-server",
    version="1.1.0",
    description=("SEPIA Speech-To-Text (STT) Server is a WebSocket based, "
        "full-duplex Python server for realtime automatic speech recognition "
        "(ASR) supporting multiple open-source ASR engines."),
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://sepia-framework.github.io/",
    license="MIT license",
    author="Florian Quirin",
    author_email="info@bytemind.de",
    keywords=[
        "speech-recognition",
        "stt",
        "asr",
        "server",
        "websocket",
        "kaldi",
        "vosk",
        "coqui",
        "whisper",
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=install_requires,
    # install extras via:
    # $ pip install -e ".[core]"
    # $ pip install sepia-stt-server[core]
    extras_require=extras_require,
)
