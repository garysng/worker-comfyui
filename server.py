"""
ComfyUI Sync Handler Example Server
Using FastAPI to implement synchronous service compatible with ComfyUI native API
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from comfyui import ComfyUIHandler
from comfyui.exceptions import (
    ComfyUIError, ComfyUIConnectionError, ComfyUITimeoutError,
    ComfyUITaskError, ComfyUIValidationError, ComfyUIServerError
)
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ComfyUI Sync Handler API",
    description="Synchronous service compatible with ComfyUI native API",
    version="1.0.0"
)

# Global handler instance
comfyui_handler = None


class PromptRequest(BaseModel):
    """Prompt request model"""
    prompt: Dict[str, Any]
    client_id: Optional[str] = None
    return_image_base64: Optional[bool] = False





@app.on_event("startup")
async def startup_event():
    """Initialize handler on startup"""
    global comfyui_handler
    
    # Initialize ComfyUI handler with configuration
    comfyui_handler = ComfyUIHandler(
        server_address=config.comfyui_server_address,
        default_timeout=config.DEFAULT_TIMEOUT
    )
    
    logger.info(f"ComfyUI Handler started, connected to: {config.comfyui_server_address}")


@app.exception_handler(ComfyUIError)
async def comfyui_error_handler(request: Request, exc: ComfyUIError):
    """Handle ComfyUI related errors"""
    if isinstance(exc, ComfyUITimeoutError):
        return JSONResponse(
            status_code=408,
            content={"error": "Task timeout", "detail": str(exc)}
        )
    elif isinstance(exc, ComfyUIConnectionError):
        return JSONResponse(
            status_code=503,
            content={"error": "ComfyUI service unavailable", "detail": str(exc)}
        )
    elif isinstance(exc, ComfyUITaskError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Task execution failed", 
                "detail": str(exc),
                "prompt_id": exc.prompt_id,
                "node_errors": exc.node_errors
            }
        )
    elif isinstance(exc, ComfyUIValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "Request validation failed", "detail": str(exc)}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal error", "detail": str(exc)}
        )


@app.post("/prompt")
async def queue_prompt(request: PromptRequest):
    """
    Compatible with ComfyUI native /prompt interface
    Difference from native API: this interface waits for task completion before returning
    """
    try:
        result = await comfyui_handler.queue_prompt_compatible(
            prompt=request.prompt,
            client_id=request.client_id
        )
        return result
    except Exception as e:
        logger.error(f"Failed to handle prompt request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt_sync")
async def submit_prompt_sync(request: PromptRequest, timeout: Optional[int] = None):
    """
    Synchronous prompt submission interface
    Returns complete task result with execution time and outputs
    
    Response format:
    - prompt_id: Task identifier  
    - status: Task status ("success" or "error")
    - execution_time: Time taken in seconds
    - outputs: ComfyUI native outputs format
    - node_errors: Any node-level errors
    """
    try:
        result = await comfyui_handler.submit_prompt_sync(
            request.prompt, 
            return_image_base64=request.return_image_base64,
            timeout=timeout
        )
        return result
    except Exception as e:
        logger.error(f"Failed to submit prompt synchronously: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/queue")
async def get_queue():
    """Get queue status (passthrough)"""
    try:
        return await comfyui_handler.get_queue_status()
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
@app.get("/history/{prompt_id}")
async def get_history(prompt_id: Optional[str] = None):
    """Get task history (passthrough)"""
    try:
        if prompt_id:
            return await comfyui_handler.get_history(prompt_id)
        else:
            # Get all history by passing empty string or None
            return await comfyui_handler.client.get_history()
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interrupt")
async def interrupt_execution():
    """Interrupt current execution (passthrough)"""
    try:
        return await comfyui_handler.interrupt_execution()
    except Exception as e:
        logger.error(f"Failed to interrupt execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        return await comfyui_handler.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
async def root():
    """Root path"""
    return {
        "message": "ComfyUI Sync Handler API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "async": "/prompt",
            "sync": "/prompt_sync",
            "queue": "/queue",
            "history": "/history",
            "interrupt": "/interrupt"
        }
    }


if __name__ == "__main__":
    import os
    # Run server
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "18188"))
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    ) 