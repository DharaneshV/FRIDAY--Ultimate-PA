import asyncio
import json
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("friday-dashboard")

app = FastAPI(title="FRIDAY Command Center Server")

# Allow all origins for the local dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# WebSocket Manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard connected. Active links: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Dashboard disconnected. Active links: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        data = json.dumps(message)
        logger.info(f"Broadcasting: {list(message.keys())}")
        
        # Gather all broadcast tasks
        tasks = [connection.send_text(data) for connection in self.active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@app.websocket("/ws/friday")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial handshake
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "data": {"status": "connected", "message": "Uplink established, sir."}
        }))
        
        while True:
            # Wait for any incoming messages from HUD
            data = await websocket.receive_text()
            logger.info(f"HUD says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/broadcast")
async def broadcast_telemetry(request: Request):
    """
    Internal endpoint for agent_friday.py to push status updates.
    """
    try:
        payload = await request.json()
        await manager.broadcast(payload)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Broadcast failure: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------------------------------------------------------------------
# Static Assets (Serve React Build)
# ---------------------------------------------------------------------------

# Path to the React project 'dist' directory
DIST_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(DIST_DIR):
    # Mount the /assets folder
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Serve index.html for all routes to handle SPA routing if any
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"status": "online", "message": "Dist folder not found. Please build the frontend."}

# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Initializing FRIDAY WebSocket Uplink on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
