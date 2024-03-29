"""Fast-API Module for SEPIA STT Server"""

from fastapi import FastAPI, Response, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from settings import SERVER_NAME, SERVER_VERSION
from launch_setup import settings
from http_api import HttpApiEndpoint, SettingsRequest
from socket_api import WebsocketApiEndpoint

# App
app = FastAPI()
app.mount("/www", StaticFiles(directory="www"))

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

http_endpoint = HttpApiEndpoint()
socket_endpoint = WebsocketApiEndpoint()

@app.get("/")
async def get():
    """Redirect to web interface or docs page"""
    return RedirectResponse(url='www/index.html')

@app.get("/online", status_code=status.HTTP_204_NO_CONTENT)
async def get_online():
    """Endpoint to check if server is online"""
    return ""

@app.get("/ping")
async def get_ping():
    """Endpoint to get some public server info"""
    return {
        "result": "success", "server": SERVER_NAME, "version": SERVER_VERSION
    }

@app.get("/settings")
async def get_settings():
    """Endpoint to GET server settings remotely"""
    return http_endpoint.handle_settings_req_get()

@app.post("/settings")
async def post_settings(req: SettingsRequest, response: Response):
    """Endpoint to set server settings remotely"""
    return http_endpoint.handle_settings_req_post(req, response)

@app.websocket("/")
async def websocket_endpoint(socket: WebSocket):
    """Endpoint to handle WebSocket connections"""
    await socket_endpoint.handle(socket)
@app.websocket("/socket")
async def websocket_endpoint_alias(socket: WebSocket):
    """Alias for WebSocket connection endpoint (e.g. for proxies that split path)"""
    await socket_endpoint.handle(socket)

print(f"SEPIA STT Server - Server running at: {settings.host}:{settings.port}")
print(f"SEPIA STT Server - Speech recognition engine: {settings.asr_engine}")
print(f"SEPIA STT Server - Models defined for engine: {len(settings.asr_model_paths)}")
