"""
ComfyUI Sync Handler - Convert ComfyUI async API to synchronous
Compatible with native API, supports passthrough but waits for task completion internally
"""

import asyncio
import logging
import time
import aiohttp
from typing import Dict, Any, Optional, List, Union
from .client import ComfyUIClient


logger = logging.getLogger(__name__)


class ComfyUIHandler:
    """
    ComfyUI Sync Handler
    
    Compatible with ComfyUI native API, but converts async operations to sync
    Supports load balancing and scheduling system to correctly determine task status
    """
    
    def __init__(self, 
                 server_address: str = "127.0.0.1:8188",
                 default_timeout: int = 300,
                 poll_interval: float = 1.0):
        """
        Initialize Handler
        
        Args:
            server_address: ComfyUI server address
            default_timeout: Default timeout in seconds
            poll_interval: Polling interval in seconds
        """
        self.client = ComfyUIClient(server_address)
        self.default_timeout = default_timeout
        self.poll_interval = poll_interval
        self._active_tasks: Dict[str, asyncio.Task] = {}
        
    async def submit_prompt_sync(self, 
                                prompt: Dict[str, Any], 
                                return_image_base64: bool = False,
                                timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit prompt synchronously and wait for completion
        
        Compatible with ComfyUI native API format, but provides synchronous response
        
        Args:
            prompt: ComfyUI workflow prompt
            timeout: Timeout, uses default if not provided
            
        Returns:
            Task result, including prompt_id, status, execution_time and outputs
        """
        timeout = timeout or self.default_timeout
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"Starting prompt processing, timeout: {timeout}s")
            
            # Submit task and wait for completion
            result = await self.client.submit_and_wait(prompt, timeout, return_base64=return_image_base64)
            
            # Calculate execution time
            end_time = time.time()
            execution_time = round(end_time - start_time, 2)
            
            # Build compatible response format
            response = {
                "prompt_id": result["prompt_id"],
                "status": "success",
                "execution_time": execution_time,
                "outputs": result["history"].get("outputs", {}),
                "node_errors": {},  # ComfyUI native error format
            }
            
            # Add image data if available
            if return_image_base64 and result.get("images"):
                response["images"] = result["images"]
            
            logger.info(f"Task {result['prompt_id']} completed successfully in {execution_time}s")
            return response
            
        except TimeoutError as e:
            logger.error(f"Task timeout: {e}")
            return {
                "status": "timeout",
                "error": str(e),
                "prompt_id": None
            }
        except Exception as e:
            logger.error(f"Task failed: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "prompt_id": None
            }
    
    async def queue_prompt_compatible(self, 
                                     prompt: Dict[str, Any], 
                                     client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compatible with ComfyUI native /prompt interface, but implements sync waiting internally
        
        This method looks like native async interface, but actually waits for task completion
        
        Args:
            prompt: ComfyUI workflow prompt
            client_id: Client ID (compatible with native API)
            
        Returns:
            Native API format compatible response
        """
        # Update client ID if provided
        if client_id:
            self.client.client_id = client_id
        
        result = await self.submit_prompt_sync(prompt)
        
        if result["status"] == "success":
            # Return ComfyUI native API compatible format
            return {
                "prompt_id": result["prompt_id"],
                "number": 1,  # Queue number (simulated)
                "node_errors": result.get("node_errors", {})
            }
        else:
            # Error case
            raise Exception(result.get("error", "Unknown error"))
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get queue status (passthrough to ComfyUI)
        """
        return await self.client.get_queue_status()
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get task history (passthrough to ComfyUI)
        """
        history = await self.client.get_history(prompt_id)
        if history is None:
            return {}
        return {prompt_id: history}
    
    async def interrupt_execution(self) -> Dict[str, Any]:
        """
        Interrupt execution (passthrough to ComfyUI)
        """
        # Need to call ComfyUI's interrupt API
        # Simple implementation for now, needs adjustment based on ComfyUI API
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.client.base_url}/interrupt") as response:
                if response.status == 200:
                    return {"status": "interrupted"}
                else:
                    raise Exception(f"Interrupt failed: {response.status}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Handler statistics for load balancing and monitoring
        """
        return {
            "active_tasks": len(self._active_tasks),
            "server_address": self.client.server_address
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check, verify if ComfyUI server is available
        """
        try:
            queue_status = await self.client.get_queue_status()
            return {
                "status": "healthy",
                "comfyui_server": self.client.server_address,
                "queue_running": len(queue_status.get("queue_running", [])),
                "queue_pending": len(queue_status.get("queue_pending", []))
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "comfyui_server": self.client.server_address
            }
