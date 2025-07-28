#!/usr/bin/env python3
"""
ComfyUI Worker Client Example
Demonstrates how to interact with the ComfyUI Handler Server
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional
import argparse


class ComfyUIWorkerClient:
    """ComfyUI Worker API Client"""
    
    def __init__(self, base_url: str = "http://localhost:18188"):
        """
        Initialize client
        
        Args:
            base_url: Handler server base URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check handler server health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get ComfyUI queue status"""
        async with self.session.get(f"{self.base_url}/queue") as response:
            return await response.json()
    
    async def get_history(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get task history
        
        Args:
            prompt_id: Specific prompt ID, or None for all history
        """
        url = f"{self.base_url}/history"
        if prompt_id:
            url += f"/{prompt_id}"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def submit_prompt_async(self, prompt: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit prompt asynchronously (ComfyUI compatible)
        Returns immediately with prompt_id
        """
        data = {
            "prompt": prompt,
            "client_id": client_id
        }
        
        async with self.session.post(
            f"{self.base_url}/prompt",
            json=data
        ) as response:
            return await response.json()
    
    async def submit_prompt_sync(self, prompt: Dict[str, Any], client_id: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit prompt synchronously
        Waits for completion and returns results
        """
        data = {
            "prompt": prompt,
            "client_id": client_id
        }
        
        # Set timeout for synchronous requests
        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None
        
        async with self.session.post(
            f"{self.base_url}/prompt_sync",
            json=data,
            timeout=timeout_obj
        ) as response:
            return await response.json()
    
    async def interrupt_execution(self) -> Dict[str, Any]:
        """Interrupt current execution"""
        async with self.session.post(f"{self.base_url}/interrupt") as response:
            return await response.json()


def create_sample_prompt() -> Dict[str, Any]:
    """Create a sample prompt for testing"""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "a beautiful landscape with mountains and lakes",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "blurry, low quality",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 8.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
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
                "filename_prefix": "ComfyUI_Worker_Test",
                "images": ["6", 0]
            }
        }
    }


async def demo_basic_operations(client: ComfyUIWorkerClient):
    """Demonstrate basic API operations"""
    print("🔍 === Basic Operations Demo ===")
    
    # 1. Health check
    print("\n1. Health Check...")
    try:
        health = await client.health_check()
        print(f"✅ Health Status: {health.get('status', 'unknown')}")
        print(f"   ComfyUI Server: {health.get('comfyui_server', 'unknown')}")
        print(f"   Queue Running: {health.get('queue_running', 0)}")
        print(f"   Queue Pending: {health.get('queue_pending', 0)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # 2. Queue status
    print("\n2. Queue Status...")
    try:
        queue = await client.get_queue_status()
        print(f"✅ Queue Info:")
        print(f"   Running: {len(queue.get('queue_running', []))}")
        print(f"   Pending: {len(queue.get('queue_pending', []))}")
    except Exception as e:
        print(f"❌ Queue status failed: {e}")
    
    # 3. History
    print("\n3. Recent History...")
    try:
        history = await client.get_history()
        if isinstance(history, dict) and history:
            recent_count = len(history)
            print(f"✅ Found {recent_count} recent tasks")
            # Show last few task IDs
            if recent_count > 0:
                recent_ids = list(history.keys())[-3:]  # Last 3 tasks
                print(f"   Recent task IDs: {recent_ids}")
        else:
            print("✅ No task history found")
    except Exception as e:
        print(f"❌ History check failed: {e}")
    
    return True


async def demo_async_workflow(client: ComfyUIWorkerClient):
    """Demonstrate asynchronous workflow"""
    print("\n🚀 === Async Workflow Demo ===")
    
    # Create sample prompt
    prompt = create_sample_prompt()
    
    print("\n1. Submitting async prompt...")
    try:
        result = await client.submit_prompt_async(prompt, client_id="demo_async")
        prompt_id = result.get("prompt_id")
        print(f"✅ Prompt submitted successfully")
        print(f"   Prompt ID: {prompt_id}")
        print(f"   Queue Position: {result.get('number', 'unknown')}")
        
        if prompt_id:
            # Monitor progress
            print("\n2. Monitoring progress...")
            max_checks = 30  # Maximum checks
            check_interval = 2  # Seconds
            
            for i in range(max_checks):
                try:
                    # Check queue status
                    queue = await client.get_queue_status()
                    running = queue.get('queue_running', [])
                    pending = queue.get('queue_pending', [])
                    
                    # Check if our task is running
                    is_running = any(task[1] == prompt_id for task in running)
                    is_pending = any(task[1] == prompt_id for task in pending)
                    
                    if is_running:
                        print(f"   [{i+1:2d}] Task is running... ⏳")
                    elif is_pending:
                        print(f"   [{i+1:2d}] Task is pending... ⏸️")
                    else:
                        # Task might be completed, check history
                        history = await client.get_history(prompt_id)
                        if history:
                            print(f"   [{i+1:2d}] Task completed! ✅")
                            print(f"   Result keys: {list(history.keys()) if isinstance(history, dict) else 'N/A'}")
                            break
                        else:
                            print(f"   [{i+1:2d}] Task status unknown... ❓")
                    
                    await asyncio.sleep(check_interval)
                
                except Exception as e:
                    print(f"   [{i+1:2d}] Error checking status: {e}")
                    await asyncio.sleep(check_interval)
            else:
                print("   ⏰ Monitoring timeout reached")
        
    except Exception as e:
        print(f"❌ Async workflow failed: {e}")


async def demo_sync_workflow(client: ComfyUIWorkerClient):
    """Demonstrate synchronous workflow"""
    print("\n⏱️ === Sync Workflow Demo ===")
    
    # Create a simpler prompt for faster execution
    simple_prompt = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            }
        }
    }
    
    print("\n1. Submitting sync prompt...")
    try:
        start_time = time.time()
        result = await client.submit_prompt_sync(
            simple_prompt, 
            client_id="demo_sync",
            timeout=60  # 60 second timeout
        )
        end_time = time.time()
        
        print(f"✅ Sync request completed in {end_time - start_time:.2f} seconds")
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   Result keys: {list(result.keys())}")
            if 'outputs' in result:
                print(f"   Output nodes: {list(result['outputs'].keys()) if result['outputs'] else 'None'}")
            if 'prompt_id' in result:
                print(f"   Prompt ID: {result['prompt_id']}")
        
    except asyncio.TimeoutError:
        print("❌ Sync request timed out")
    except Exception as e:
        print(f"❌ Sync workflow failed: {e}")


async def demo_interrupt_workflow(client: ComfyUIWorkerClient):
    """Demonstrate interrupt functionality"""
    print("\n🛑 === Interrupt Demo ===")
    
    # First check if there's anything to interrupt
    queue = await client.get_queue_status()
    running_tasks = queue.get('queue_running', [])
    
    if running_tasks:
        print(f"Found {len(running_tasks)} running tasks")
        print("Sending interrupt signal...")
        
        try:
            result = await client.interrupt_execution()
            print(f"✅ Interrupt signal sent")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"❌ Interrupt failed: {e}")
    else:
        print("No running tasks to interrupt")


async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="ComfyUI Worker Client Demo")
    parser.add_argument(
        "--url", 
        default="http://localhost:18188",
        help="Handler server URL (default: http://localhost:18188)"
    )
    parser.add_argument(
        "--demo",
        choices=["basic", "async", "sync", "interrupt", "all"],
        default="all",
        help="Which demo to run (default: all)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    print(f"🔌 Connecting to ComfyUI Worker at: {args.url}")
    print(f"🎯 Running demo: {args.demo}")
    print("-" * 50)
    
    try:
        async with ComfyUIWorkerClient(args.url) as client:
            # Basic operations (always run first)
            if args.demo in ["basic", "all"]:
                success = await demo_basic_operations(client)
                if not success:
                    print("\n❌ Basic operations failed. Please check if the server is running.")
                    return
            
            # Run specific demos
            if args.demo in ["async", "all"]:
                await demo_async_workflow(client)
            
            if args.demo in ["sync", "all"]:
                await demo_sync_workflow(client)
            
            if args.demo in ["interrupt", "all"]:
                await demo_interrupt_workflow(client)
    
    except aiohttp.ClientConnectorError:
        print(f"\n❌ Cannot connect to {args.url}")
        print("   Please make sure the ComfyUI Worker is running:")
        print("   docker-compose up  # or")
        print("   ./start.sh")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print("\n📚 Available endpoints:")
    print(f"   • Health: {args.url}/health")
    print(f"   • Queue: {args.url}/queue") 
    print(f"   • History: {args.url}/history")
    print(f"   • API Docs: {args.url}/docs")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
