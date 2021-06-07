"""Fast-API Module for SEPIA STT Server"""

import os

from fastapi import FastAPI, Response, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from settings import SettingsFile
from http_api import HttpApiEndpoint, SettingsRequest
from socket_api import WebsocketApiEndpoint

# Server constants
SERVER_NAME = "SEPIA STT Server V2 BETA"
SERVER_VERSION = "0.0.1"

# Run arguments (via ENV)
custom_settings = os.getenv("SEPIA_STT_SETTINGS")

#Load settings
settings = SettingsFile(custom_settings)

# App
app = FastAPI()
app.mount("/www", StaticFiles(directory="www"))

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

http_endpoint = HttpApiEndpoint()
socket_endpoint = WebsocketApiEndpoint()

@app.get("/")
async def get():
    """Redirect to web interface or docs page"""
    return HTMLResponse("""
        <p><a href='www/index.html'>Open Web Interface</a></p>
        <p><a href='docs'>Open Docs</a></p>
    """)
    #<script>window.location.href = 'www/index.html';</script>

@app.get("/online", status_code=status.HTTP_204_NO_CONTENT)
async def get_online():
    """Endpoint to check if server is online"""
    return ""

@app.get("/ping")
async def get_ping():
    """Endpoint to get some public server info"""
    return {"result": "success", "server": SERVER_NAME, "version": SERVER_VERSION}

@app.post("/settings")
async def post_settings(req: SettingsRequest, response: Response):
    """Endpoint to set server settings remotely"""
    return http_endpoint.handle_settings_req(req, response)

@app.websocket("/")
async def websocket_endpoint(socket: WebSocket):
    """Endpoint to handle WebSocket connections"""
    await socket_endpoint.handle(socket)
