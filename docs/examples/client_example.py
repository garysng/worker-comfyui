#!/usr/bin/env python3
"""
ComfyUI Worker Client Example
Demonstrates how to use the ComfyUI Worker Handler API
"""

import asyncio
import aiohttp
import time
import json
from typing import Optional, Dict, Any


class ComfyUIWorkerClient:
    """Simple client for ComfyUI Worker Handler"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Health check failed: {response.status}")
    
    async def submit_prompt_sync(self, prompt: Dict[str, Any], 
                                client_id: Optional[str] = None,
                                return_image_base64: bool = False,
                                timeout: int = 300) -> Dict[str, Any]:
        """Submit prompt synchronously"""
        data = {
            "prompt": prompt,
            "return_image_base64": return_image_base64
        }
        if client_id:
            data["client_id"] = client_id
        
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        async with self.session.post(
            f"{self.base_url}/prompt_sync",
            json=data,
            timeout=timeout_obj
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Request failed ({response.status}): {error_text}")
    
    async def submit_prompt_async(self, prompt: Dict[str, Any],
                                 client_id: Optional[str] = None) -> Dict[str, Any]:
        """Submit prompt asynchronously (ComfyUI compatible)"""
        data = {
            "prompt": prompt
        }
        if client_id:
            data["client_id"] = client_id
        
        async with self.session.post(
            f"{self.base_url}/prompt",
            json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Request failed ({response.status}): {error_text}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        async with self.session.get(f"{self.base_url}/queue") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Queue status request failed: {response.status}")
    
    async def get_history(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution history"""
        url = f"{self.base_url}/history"
        if prompt_id:
            url += f"/{prompt_id}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"History request failed: {response.status}")
    
    async def interrupt_execution(self) -> Dict[str, Any]:
        """Interrupt current execution"""
        async with self.session.post(f"{self.base_url}/interrupt") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Interrupt request failed: {response.status}")


def create_simple_flux_prompt(text: str = "beautiful landscape", 
                             width: int = 512, 
                             height: int = 512,
                             steps: int = 20,
                             cfg: float = 8.0,
                             seed: Optional[int] = None) -> Dict[str, Any]:
    """Create a simple FLUX generation prompt"""
    import random
    
    if seed is None:
        seed = random.randint(1000000, 9999999999)
    
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "flux1-dev-fp8.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": text
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "blurry, low quality, bad anatomy"
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": height,
                "width": width
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1.0,
                "latent_image": ["4", 0],
                "model": ["1", 0],
                "negative": ["3", 0],
                "positive": ["2", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": seed,
                "steps": steps
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "flux_output",
                "images": ["6", 0]
            }
        }
    }


async def example_synchronous_generation():
    """Example: Synchronous image generation"""
    print("=== Synchronous Generation Example ===")
    
    # Configure your server URL
    server_url = "https://your-comfyui-worker.example.com"
    
    async with ComfyUIWorkerClient(server_url) as client:
        # Check server health
        try:
            health = await client.health_check()
            print(f"Server status: {health.get('status', 'unknown')}")
        except Exception as e:
            print(f"Health check failed: {e}")
            return
        
        # Create a simple prompt
        prompt = create_simple_flux_prompt(
            text="a beautiful sunset over mountains",
            width=768,
            height=512,
            steps=20
        )
        
        print("Submitting prompt for synchronous generation...")
        start_time = time.time()
        
        try:
            result = await client.submit_prompt_sync(
                prompt=prompt,
                client_id="example_client",
                timeout=300
            )
            
            duration = time.time() - start_time
            
            print(f"✅ Generation completed in {duration:.2f}s")
            print(f"Prompt ID: {result.get('prompt_id')}")
            print(f"Execution time: {result.get('execution_time')}s")
            print(f"Status: {result.get('status')}")
            
            # Print output information
            outputs = result.get('outputs', {})
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    images = node_output['images']
                    print(f"Node {node_id} generated {len(images)} image(s):")
                    for img in images:
                        print(f"  - {img.get('filename', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")


async def example_asynchronous_generation():
    """Example: Asynchronous image generation (ComfyUI compatible)"""
    print("\n=== Asynchronous Generation Example ===")
    
    server_url = "https://your-comfyui-worker.example.com"
    
    async with ComfyUIWorkerClient(server_url) as client:
        # Create prompt
        prompt = create_simple_flux_prompt(
            text="a cute cat sitting in a garden",
            steps=15
        )
        
        print("Submitting prompt for asynchronous generation...")
        
        try:
            # Submit prompt
            submit_result = await client.submit_prompt_async(
                prompt=prompt,
                client_id="async_example"
            )
            
            prompt_id = submit_result.get('prompt_id')
            print(f"Prompt submitted with ID: {prompt_id}")
            
            # Monitor queue status
            print("Monitoring queue status...")
            while True:
                queue_status = await client.get_queue_status()
                
                running = queue_status.get('queue_running', [])
                pending = queue_status.get('queue_pending', [])
                
                print(f"Queue status - Running: {len(running)}, Pending: {len(pending)}")
                
                # Check if our prompt is still in queue
                our_prompt_running = any(item[1] == prompt_id for item in running)
                our_prompt_pending = any(item[1] == prompt_id for item in pending)
                
                if not our_prompt_running and not our_prompt_pending:
                    print("Prompt completed or not found in queue")
                    break
                
                await asyncio.sleep(2)  # Poll every 2 seconds
            
            # Get final result from history
            print("Fetching result from history...")
            history = await client.get_history(prompt_id)
            
            if prompt_id in history:
                result = history[prompt_id]
                print(f"✅ Generation completed")
                print(f"Status: {result.get('status', {}).get('status_str', 'unknown')}")
                
                outputs = result.get('outputs', {})
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        images = node_output['images']
                        print(f"Node {node_id} generated {len(images)} image(s)")
            else:
                print("❌ Result not found in history")
                
        except Exception as e:
            print(f"❌ Generation failed: {e}")


async def example_with_base64_images():
    """Example: Getting images as base64 data"""
    print("\n=== Base64 Images Example ===")
    
    server_url = "https://your-comfyui-worker.example.com"
    
    async with ComfyUIWorkerClient(server_url) as client:
        # Create a small prompt for faster processing
        prompt = create_simple_flux_prompt(
            text="simple geometric pattern",
            width=256,
            height=256,
            steps=10
        )
        
        print("Generating image with base64 output...")
        
        try:
            result = await client.submit_prompt_sync(
                prompt=prompt,
                return_image_base64=True,  # Request base64 images
                timeout=180
            )
            
            print(f"✅ Generation completed")
            
            # Check if images are included in response
            if 'images' in result:
                images_data = result['images']
                print(f"Received images data for {len(images_data)} nodes")
                
                for node_id, images in images_data.items():
                    print(f"Node {node_id}: {len(images)} image(s)")
                    for i, img_data in enumerate(images):
                        if 'base64' in img_data:
                            base64_data = img_data['base64']
                            print(f"  Image {i+1}: {len(base64_data)} characters of base64 data")
                            
                            # You can save the image like this:
                            # import base64
                            # with open(f"output_{node_id}_{i}.png", "wb") as f:
                            #     f.write(base64.b64decode(base64_data))
            else:
                print("No base64 images in response")
                
        except Exception as e:
            print(f"❌ Generation failed: {e}")


async def example_queue_management():
    """Example: Queue management operations"""
    print("\n=== Queue Management Example ===")
    
    server_url = "https://your-comfyui-worker.example.com"
    
    async with ComfyUIWorkerClient(server_url) as client:
        try:
            # Get current queue status
            queue_status = await client.get_queue_status()
            print("Current queue status:")
            print(f"  Running: {len(queue_status.get('queue_running', []))}")
            print(f"  Pending: {len(queue_status.get('queue_pending', []))}")
            
            # Submit a prompt
            prompt = create_simple_flux_prompt("test image", steps=5)
            submit_result = await client.submit_prompt_async(prompt)
            prompt_id = submit_result.get('prompt_id')
            print(f"\nSubmitted test prompt: {prompt_id}")
            
            # Wait a moment then interrupt if needed
            await asyncio.sleep(2)
            
            # Check if we want to interrupt
            queue_status = await client.get_queue_status()
            if len(queue_status.get('queue_running', [])) > 0:
                print("Interrupting current execution...")
                interrupt_result = await client.interrupt_execution()
                print(f"Interrupt result: {interrupt_result}")
            
        except Exception as e:
            print(f"❌ Queue management failed: {e}")


async def main():
    """Run all examples"""
    print("ComfyUI Worker Client Examples")
    print("=" * 50)
    
    # Note: Update the server URL in each example function
    print("⚠️  Please update the server_url in each example function before running")
    
    try:
        # Run examples
        await example_synchronous_generation()
        await asyncio.sleep(1)
        
        await example_asynchronous_generation()
        await asyncio.sleep(1)
        
        await example_with_base64_images()
        await asyncio.sleep(1)
        
        await example_queue_management()
        
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
    
    print("\n✅ All examples completed")


if __name__ == "__main__":
    asyncio.run(main()) 