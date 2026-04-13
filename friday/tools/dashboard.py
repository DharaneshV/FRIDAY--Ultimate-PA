"""
Dashboard tools — integration with the FastAPI WebSocket HUD.
"""

import httpx
import json
import logging

logger = logging.getLogger("mcp-dashboard")

DASHBOARD_URL = "http://127.0.0.1:8000/broadcast"

def register(mcp):

    @mcp.tool()
    async def broadcast_telemetry(payload_json: str) -> str:
        """
        Broadcasting telemetry or status updates to the Visual HUD.
        payload_json MUST be a valid JSON string.
        """
        try:
            # Validate JSON
            data = json.loads(payload_json)
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(DASHBOARD_URL, json=data)
                if response.status_code == 200:
                    return "Telemetry broadcast successful, sir."
                else:
                    return f"Broadcast failed with status {response.status_code}."
        except json.JSONDecodeError:
            return "Error: payload_json must be valid JSON."
        except Exception as e:
            return f"Internal broadcast error: {str(e)}"

    @mcp.tool()
    async def open_hud() -> str:
        """
        Initializes and opens the Friday Command Center HUD in the primary web browser.
        """
        import webbrowser
        hud_url = "http://localhost:8000"
        try:
            # We assume the dashboard_server.py is running on port 8000
            webbrowser.open(hud_url)
            return "Command Center HUD initialized and displayed on your primary monitor, boss."
        except Exception as e:
            return f"Failed to initialize HUD: {str(e)}"
