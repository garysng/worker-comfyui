"""
ComfyUI API Client
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Union
import aiohttp
import websockets


logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI API client for communicating with ComfyUI server"""
    
    def __init__(self, server_address: str = "127.0.0.1:8188", client_id: Optional[str] = None):
        """
        Initialize ComfyUI client
        
        Args:
            server_address: ComfyUI server address
            client_id: Client ID, auto-generated if not provided
        """
        self.server_address = server_address
        self.client_id = client_id or self._generate_client_id()
        self.base_url = f"http://{server_address}"
        self.ws_url = f"ws://{server_address}/ws"
        
    def _generate_client_id(self) -> str:
        """Generate client ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        """
        Submit prompt to ComfyUI queue
        
        Args:
            prompt: ComfyUI workflow prompt
            
        Returns:
            prompt_id: Submitted task ID
        """
        data = {
            "prompt": prompt,
            "client_id": self.client_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/prompt", json=data) as response:
                if response.status != 200:
                    raise Exception(f"Failed to submit prompt: {response.status}")
                
                result = await response.json()
                return result["prompt_id"]
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/queue") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get queue status: {response.status}")
                return await response.json()
    
    async def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task history
        
        Args:
            prompt_id: Task ID
            
        Returns:
            Task history, None if task is not completed
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as response:
                if response.status != 200:
                    return None
                
                history = await response.json()
                return history.get(prompt_id)
    
    async def wait_for_completion(self, prompt_id: str, timeout: int = 300, poll_interval: float = 1.0) -> Dict[str, Any]:
        """
        Wait for task completion
        
        Args:
            prompt_id: Task ID
            timeout: Timeout in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: Task timeout
            Exception: Task failed
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check history for results
            history = await self.get_history(prompt_id)
            if history is not None:
                # Task completed
                if "outputs" in history:
                    return history
                elif "status" in history and history["status"].get("status_str") == "error":
                    raise Exception(f"Task execution failed: {history.get('status', {}).get('messages', [])}")
            
            # Check queue status
            queue_status = await self.get_queue_status()
            running = queue_status.get("queue_running", [])
            pending = queue_status.get("queue_pending", [])
            
            # Check if task is still in queue
            found_in_queue = False
            for item in running + pending:
                if item[1] == prompt_id:
                    found_in_queue = True
                    break
            
            if not found_in_queue:
                # Task not in queue, check history again
                history = await self.get_history(prompt_id)
                if history is not None:
                    return history
                else:
                    raise Exception(f"Task {prompt_id} not found")
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Task {prompt_id} timed out")
    
    async def get_output_images_info(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get output images information from task history (metadata only)
        
        Args:
            history: Task history
            
        Returns:
            Dictionary containing image metadata by node_id
        """
        images_info = {}
        outputs = history.get("outputs", {})
        
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                images_info[node_id] = []
                for image in node_output["images"]:
                    # Only return metadata, not binary data
                    image_info = {
                        "filename": image["filename"],
                        "subfolder": image.get("subfolder", ""),
                        "type": image.get("type", "output"),
                        "url": self._build_image_url(image)
                    }
                    images_info[node_id].append(image_info)
        
        return images_info
    
    def _build_image_url(self, image_info: Dict[str, Any]) -> str:
        """Build image URL for accessing images"""
        filename = image_info["filename"]
        subfolder = image_info.get("subfolder", "")
        image_type = image_info.get("type", "output")
        
        url = f"{self.base_url}/view?filename={filename}&type={image_type}"
        if subfolder:
            url += f"&subfolder={subfolder}"
        
        return url
    
    async def get_output_images_base64(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get output images as base64 encoded strings (if needed)
        
        Args:
            history: Task history
            
        Returns:
            Dictionary containing base64 encoded images by node_id
        """
        import base64
        
        images_b64 = {}
        outputs = history.get("outputs", {})
        
        async with aiohttp.ClientSession() as session:
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    images_b64[node_id] = []
                    for image in node_output["images"]:
                        filename = image["filename"]
                        subfolder = image.get("subfolder", "")
                        image_type = image.get("type", "output")
                        
                        # Build image URL
                        url_params = {
                            "filename": filename,
                            "type": image_type
                        }
                        if subfolder:
                            url_params["subfolder"] = subfolder
                        
                        url = f"{self.base_url}/view"
                        async with session.get(url, params=url_params) as response:
                            if response.status == 200:
                                image_bytes = await response.read()
                                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                images_b64[node_id].append({
                                    "filename": filename,
                                    "subfolder": subfolder,
                                    "type": image_type,
                                    "data": image_b64
                                })
        
        return images_b64
    
    async def submit_and_wait(self, prompt: Dict[str, Any], timeout: int = 300, 
                             return_base64: bool = False) -> Dict[str, Any]:
        """
        Submit prompt and wait for completion (synchronous approach)
        
        Args:
            prompt: ComfyUI workflow prompt
            timeout: Timeout in seconds
            return_base64: Whether to return images as base64 (default: False, returns metadata only)
            
        Returns:
            Dictionary containing task result and image information
        """
        # Submit task
        prompt_id = await self.queue_prompt(prompt)
        logger.info(f"Task submitted, ID: {prompt_id}")
        
        # Wait for completion
        history = await self.wait_for_completion(prompt_id, timeout)
        logger.info(f"Task {prompt_id} completed")
        
        # Get image information (metadata only by default)
        if return_base64:
            images = await self.get_output_images_base64(history)
        else:
            images = await self.get_output_images_info(history)
        
        return {
            "prompt_id": prompt_id,
            "history": history,
            "images": images
        } 