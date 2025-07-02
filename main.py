from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import staticfiles
from fastapi.websockets import WebSocket, WebSocketDisconnect

from manager import MeetingManager

app = FastAPI()

# Mount static files
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Force HTTPS in url_for()
from starlette.requests import Request as StarletteRequest
def force_https_url_for(request: StarletteRequest, name: str, **path_params):
    return request.url_for(name, **path_params).replace("http://", "https://")
templates.env.globals['url_for'] = lambda name, **path_params: (
    lambda request: request.url_for(name, **path_params).replace("http://", "https://")
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Meeting manager
meeting_manager = MeetingManager()

# Routes
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

@app.get("/room/{roomName}")
def get_video(request: Request, roomName: str):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws/{client_id}")
async def connect_websocket(websocket: WebSocket, client_id: str):
    await meeting_manager.join(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await meeting_manager.rooms[client_id].broadcast(data, websocket)
    except WebSocketDisconnect:
        meeting_manager.leave(client_id, websocket)
