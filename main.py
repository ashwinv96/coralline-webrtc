from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from manager import MeetingManager

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Override url_for to enforce HTTPS
def https_url_for(request: Request, name: str, **path_params):
    url = request.url_for(name, **path_params)
    return str(url).replace("http://", "https://")

# Inject the HTTPS url_for into template globals
templates.env.globals["https_url_for"] = https_url_for

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
meeting_manager = MeetingManager()

# Routes
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "https_url_for": https_url_for})

@app.get("/room/{roomName}")
def get_video(request: Request, roomName: str):
    return templates.TemplateResponse("index.html", {"request": request, "https_url_for": https_url_for})

@app.websocket("/ws/{client_id}")
async def connect_websocket(websocket: WebSocket, client_id: str):
    await meeting_manager.join(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await meeting_manager.rooms[client_id].broadcast(data, websocket)
    except WebSocketDisconnect:
        meeting_manager.leave(client_id, websocket)
