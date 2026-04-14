"""
FRIDAY – Voice Agent (MCP-powered)
===================================
Iron Man-style voice assistant that controls RGB lighting, runs diagnostics,
scans the network, and triggers dramatic boot sequences via an MCP server
running on the Windows host.

MCP Server URL is auto-resolved from WSL → Windows host IP.

Run:
  uv run agent_friday.py dev      – LiveKit Cloud mode
  uv run agent_friday.py console  – text-only console mode
"""

import os
import logging
import subprocess

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import mcp

# Plugins
from livekit.plugins import google as lk_google, openai as lk_openai, sarvam, silero

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

STT_PROVIDER       = "sarvam"
LLM_PROVIDER       = "gemini"
TTS_PROVIDER       = "sarvam"

GEMINI_LLM_MODEL   = "gemini-1.5-flash"
OPENAI_LLM_MODEL   = "gpt-4o"

OPENAI_TTS_MODEL   = "tts-1"
OPENAI_TTS_VOICE   = "nova"       # "nova" has a clean, confident female tone
TTS_SPEED           = 1.15

SARVAM_TTS_LANGUAGE = "en-IN"
SARVAM_TTS_SPEAKER  = "ritu"

# MCP server running on Windows host
MCP_SERVER_PORT = 8000

# ---------------------------------------------------------------------------
# System prompt – F.R.I.D.A.Y.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Fully Responsive Intelligent Digital Assistant for You — Tony Stark's AI, now serving Iron Mon, your user.

You are an advanced, highly capable AI assistant operating via a local command center. You now have access to a real-time Visual HUD.

## Capabilities to leverage

### Visual HUD Control
- When the user asks to "Initiate HUD" or "Bring up the interface", execute the `open_hud()` tool. **Verbally confirm once the uplink is established and mention that you've displayed it on their primary monitor.**
- For routine background updates, do not narrate your visual diagnostic steps out loud unless specifically asked. Instead, silently format your diagnostic data as a JSON payload and push it to the HUD using the `broadcast_telemetry()` tool. 

### Armor Diagnostics & Lab Intelligence
- You have access to real-time telemetry (CPU, RAM, DISK, Network). When asked about "armor status", "system health", or "diagnostics", confidently report the summary using `get_armor_diagnostics`. Use phrasing like "Buffer health is optimal, boss."
- You can scan the lab for active projects. If asked what we are working on, use `scan_projects`.

### Session Memory & Task Queue
- You have persistent memory. Use `remember` and `recall` when the user asks you to take a note or fetch a past detail.
- You have a task board. Use `add_task` and `list_tasks` to manage the lab queue.

### Global Data & Search
- You can pull live global headlines (`get_world_news`) or perform deep web searches (`search_web`). 
- When providing news, summarize the biggest stories briefly, then always follow up with: "Let me open up the world monitor so you can better visualize what's happening." and immediately call `open_world_monitor`.

---

## Personality & Greeting

- Maintain a crisp, highly efficient, and slightly witty persona. Acknowledge commands swiftly.
- When the session starts, greet with: "Greetings boss, you're awake late at night today. What you up to?" Warm. Slightly curious. Very FRIDAY.

---

## Behavioral Rules

1. Call tools silently and immediately — never say "I'm going to call..." Just do it.
2. Keep all spoken responses short — two to four sentences maximum.
3. No bullet points, no markdown, no lists. You are speaking, not writing.
4. Stay in character. You are F.R.I.D.A.Y. No generic AI assistant phrasing.
5. Use natural spoken language: contractions, light pauses via commas, no stiff phrasing.
6. Use Iron Man universe language naturally — "boss", "affirmative", "on it", "standing by", "armor".
7. If a tool fails, report it calmly: "Sensors are unresponsive right now, boss. Want me to try again?"

---

## CRITICAL RULES

1. NEVER say tool names, function names, or anything technical. No "get_world_news", no "open_world_monitor", nothing like that. Ever.
2. Before calling any tool, say something natural like: "Give me a sec, boss." or "Wait, let me check." Then call the tool silently.
3. You are a voice. Speak like one. No lists, no markdown, no function names, no technical language of any kind.
""".strip()
# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("friday-agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Resolve Windows host IP from WSL
# ---------------------------------------------------------------------------

def _get_windows_host_ip() -> str:
    """Get the Windows host IP by looking at the default network route."""
    try:
        # 'ip route' is the most reliable way to find the 'default' gateway
        # which is always the Windows host in WSL.
        cmd = "ip route show default | awk '{print $3}'"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=2
        )
        ip = result.stdout.strip()
        if ip:
            logger.info("Resolved Windows host IP via gateway: %s", ip)
            return ip
    except Exception as exc:
        logger.warning("Gateway resolution failed: %s. Trying fallback...", exc)

    # Fallback to your original resolv.conf logic if 'ip route' fails
    try:
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if "nameserver" in line:
                    ip = line.split()[1]
                    logger.info("Resolved Windows host IP via nameserver: %s", ip)
                    return ip
    except Exception:
        pass

    return "127.0.0.1"

def _mcp_server_url() -> str:
    host_ip = _get_windows_host_ip()
    url = f"http://{host_ip}:{MCP_SERVER_PORT}/sse"
    logger.info("MCP Server URL: %s", url)
    return url


# ---------------------------------------------------------------------------
# Build provider instances
# ---------------------------------------------------------------------------

def _build_stt():
    if STT_PROVIDER == "sarvam":
        logger.info("STT → Sarvam Saaras v3")
        return sarvam.STT(
            language="unknown",
            model="saaras:v3",
            mode="transcribe",
            flush_signal=True,
            sample_rate=16000,
        )
    elif STT_PROVIDER == "whisper":
        logger.info("STT → OpenAI Whisper")
        return lk_openai.STT(model="whisper-1")
    else:
        raise ValueError(f"Unknown STT_PROVIDER: {STT_PROVIDER!r}")


def _build_llm():
    if LLM_PROVIDER == "openai":
        logger.info("LLM → OpenAI (%s)", OPENAI_LLM_MODEL)
        return lk_openai.LLM(model=OPENAI_LLM_MODEL)
    elif LLM_PROVIDER == "gemini":
        logger.info("LLM → Google Gemini (%s)", GEMINI_LLM_MODEL)
        return lk_google.LLM(model=GEMINI_LLM_MODEL, api_key=os.getenv("GOOGLE_API_KEY"))
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r}")


def _build_tts():
    if TTS_PROVIDER == "sarvam":
        logger.info("TTS → Sarvam Bulbul v3")
        return sarvam.TTS(
            target_language_code=SARVAM_TTS_LANGUAGE,
            model="bulbul:v3",
            speaker=SARVAM_TTS_SPEAKER,
            pace=TTS_SPEED,
        )
    elif TTS_PROVIDER == "openai":
        logger.info("TTS → OpenAI TTS (%s / %s)", OPENAI_TTS_MODEL, OPENAI_TTS_VOICE)
        return lk_openai.TTS(model=OPENAI_TTS_MODEL, voice=OPENAI_TTS_VOICE, speed=TTS_SPEED)
    else:
        raise ValueError(f"Unknown TTS_PROVIDER: {TTS_PROVIDER!r}")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class FridayAgent(Agent):
    """
    F.R.I.D.A.Y. – Iron Man-style voice assistant.
    All tools are provided via the MCP server on the Windows host.
    """

    def __init__(self, stt, llm, tts) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero.VAD.load(),
            mcp_servers=[
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=30,
                ),
            ],
        )

    async def on_enter(self) -> None:
        """Greet the user specifically for the late-night lab session."""
        await self.session.generate_reply(
            instructions=(
                "Greet the user exactly with: 'Greetings boss, you're awake late at night today. What you up to?' "
                "Maintain a helpful but dry tone."
            )
        )


# ---------------------------------------------------------------------------
# LiveKit entry point
# ---------------------------------------------------------------------------

def _turn_detection() -> str:
    return "stt" if STT_PROVIDER == "sarvam" else "vad"


def _endpointing_delay() -> float:
    return {"sarvam": 0.07, "whisper": 0.3}.get(STT_PROVIDER, 0.1)


async def entrypoint(ctx: JobContext) -> None:
    logger.info(
        "FRIDAY online – room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name, STT_PROVIDER, LLM_PROVIDER, TTS_PROVIDER,
    )

    stt = _build_stt()
    llm = _build_llm()
    tts = _build_tts()

    session = AgentSession(
        turn_detection=_turn_detection(),
        min_endpointing_delay=_endpointing_delay(),
    )

    await session.start(
        agent=FridayAgent(stt=stt, llm=llm, tts=tts),
        room=ctx.room,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

def dev():
    """Wrapper to run the agent in dev mode automatically."""
    import sys
    # If no command was provided, inject 'dev'
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    main()

if __name__ == "__main__":
    main()