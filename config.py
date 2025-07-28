"""
ComfyUI Sync Handler Configuration
"""

import os
from typing import Optional


class Config:
    """Configuration class"""
    
    # ComfyUI server configuration
    COMFYUI_SERVER_HOST: str = os.getenv("COMFYUI_SERVER_HOST", "127.0.0.1")
    COMFYUI_SERVER_PORT: int = int(os.getenv("COMFYUI_SERVER_PORT", "8188"))
    
    @property
    def comfyui_server_address(self) -> str:
        return f"{self.COMFYUI_SERVER_HOST}:{self.COMFYUI_SERVER_PORT}"
    
    # Handler configuration
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "600"))
    POLL_INTERVAL: float = float(os.getenv("POLL_INTERVAL", "1.0"))
    
    # Server configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Development mode
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


# Global configuration instance
config = Config()


# Environment variables example (can be set in .env file)
ENV_EXAMPLE = """
# ComfyUI server configuration
COMFYUI_SERVER_HOST=127.0.0.1
COMFYUI_SERVER_PORT=8188

# Handler configuration
DEFAULT_TIMEOUT=600
POLL_INTERVAL=1.0   

# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Logging configuration
LOG_LEVEL=INFO

# Development mode
DEBUG=False
""" 