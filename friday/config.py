"""
Configuration — load environment variables and app-wide settings.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("friday.config")

class _Settings:
    def __init__(self):
        # Server identity
        self.SERVER_NAME: str = os.getenv("SERVER_NAME", "Friday")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

        # LLM / Voice (Used by agent_friday.py, but good to have here if MCP needs them)
        self.LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
        self.LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
        self.LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
        self.GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        
        # Web Search tools
        self.TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
        self.SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
        self.SEARCH_API_KEY: str = os.getenv("SEARCH_API_KEY", "") # Legacy fallback

        # Memory System
        self.MEMORY_FILE: str = os.getenv("MEMORY_FILE", "friday_memory.json")

    def validate(self):
        """Warns about missing but recommended environment variables at startup."""
        missing = []
        if not self.TAVILY_API_KEY and not self.SERPER_API_KEY:
            missing.append("Tavily/Serper APIs (web search will run in degraded scrape mode)")
        
        if missing:
            logger.warning("FRIDAY config warning - Missing keys for full capability: %s", ", ".join(missing))

config = _Settings()
config.validate()
