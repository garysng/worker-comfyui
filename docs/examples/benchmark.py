#!/usr/bin/env python3
"""
ComfyUI Worker Benchmark Tool
Stress testing tool based on curl examples
"""

import asyncio
import aiohttp
import json
import time
import random
import argparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from statistics import mean, median


@dataclass
class TestResult:
    """Single test result"""
    prompt_id: str
    status: str
    execution_time: float
    response_time: float
    success: bool
    prompt_name: str
    test_id: int
    error: Optional[str] = None


class ComfyUIBenchmark:
    """ComfyUI Worker benchmark testing class"""
    
    def __init__(self, base_url: str):
        """
        Initialize benchmark testing
        
        Args:
            base_url: ComfyUI Worker server address
        """
        self.base_url = base_url.rstrip('/')
        
    def generate_prompt_variations(self, base_template: str, count: int) -> List[Dict[str, Any]]:
        """Generate multiple prompt variations for testing"""
        prompts = []
        
        # Define text variations for different prompt types
        text_variations = {
            "pretty_girl": [
                "beautiful young woman",
                "pretty girl with long hair",
                "attractive female portrait",
                "cute girl smiling",
                "elegant woman face",
                "lovely girl with blue eyes",
                "charming woman portrait",
                "beautiful female model",
                "pretty asian girl",
                "gorgeous woman headshot"
            ],
            "landscape": [
                "mountain landscape at sunset",
                "forest with lake reflection",
                "desert dunes golden hour",
                "ocean waves on beach",
                "snow covered peaks",
                "rolling green hills",
                "autumn forest colors",
                "tropical island paradise",
                "canyon rock formations",
                "meadow wildflowers spring"
            ],
            "fast_test": [
                "simple red circle",
                "blue square shape",
                "green triangle test",
                "yellow star icon",
                "purple heart symbol",
                "orange diamond shape",
                "pink flower simple",
                "white cloud basic",
                "black dot center",
                "gray line horizontal"
            ]
        }
        
        base_prompts = self.get_prompt_templates()
        template = base_prompts.get(base_template, base_prompts["pretty_girl"])
        texts = text_variations.get(base_template, text_variations["pretty_girl"])
        
        for i in range(count):
            # Create a copy of the template
            prompt = json.loads(json.dumps(template))
            
            # Vary the text prompt
            text_index = i % len(texts)
            prompt["6"]["inputs"]["text"] = texts[text_index]
            
            # Vary other parameters
            prompt["3"]["inputs"]["seed"] = random.randint(1000000, 9999999999)
            prompt["3"]["inputs"]["cfg"] = random.uniform(6.0, 10.0)
            
            # Vary steps slightly for performance testing
            base_steps = template["3"]["inputs"]["steps"]
            prompt["3"]["inputs"]["steps"] = max(5, base_steps + random.randint(-5, 5))
            
            # Vary image dimensions slightly
            base_width = template["5"]["inputs"]["width"]
            base_height = template["5"]["inputs"]["height"]
            
            # Keep aspect ratio but vary size slightly
            scale_factor = random.uniform(0.8, 1.2)
            new_width = int(base_width * scale_factor)
            new_height = int(base_height * scale_factor)
            
            # Round to multiples of 64 for stability
            new_width = ((new_width + 31) // 64) * 64
            new_height = ((new_height + 31) // 64) * 64
            
            prompt["5"]["inputs"]["width"] = new_width
            prompt["5"]["inputs"]["height"] = new_height
            
            # Update filename prefix with index
            original_prefix = template["9"]["inputs"]["filename_prefix"]
            prompt["9"]["inputs"]["filename_prefix"] = f"{original_prefix}_{i+1:04d}"
            
            prompts.append(prompt)
        
        return prompts
        
    def get_prompt_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined prompt templates"""
        return {
            "pretty_girl": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "cfg": 8,
                        "denoise": 1,
                        "latent_image": ["5", 0],
                        "model": ["4", 0],
                        "negative": ["7", 0],
                        "positive": ["6", 0],
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "seed": 123456,
                        "steps": 20
                    }
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "flux1-dev-fp8.safetensors"
                    }
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "batch_size": 1,
                        "height": 512,
                        "width": 512
                    }
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "pretty girl"
                    }
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "text, watermark"
                    }
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    }
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": "ComfyUI",
                        "images": ["8", 0]
                    }
                }
            },
            
            "landscape": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "cfg": 7,
                        "denoise": 1,
                        "latent_image": ["5", 0],
                        "model": ["4", 0],
                        "negative": ["7", 0],
                        "positive": ["6", 0],
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "seed": 123456,
                        "steps": 15
                    }
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "flux1-dev-fp8.safetensors"
                    }
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "batch_size": 1,
                        "height": 768,
                        "width": 1024
                    }
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "beautiful mountain landscape, sunset, realistic"
                    }
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "blurry, low quality, artifacts"
                    }
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    }
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": "landscape",
                        "images": ["8", 0]
                    }
                }
            },
            
            "fast_test": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "cfg": 6,
                        "denoise": 1,
                        "latent_image": ["5", 0],
                        "model": ["4", 0],
                        "negative": ["7", 0],
                        "positive": ["6", 0],
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "seed": 123456,
                        "steps": 5
                    }
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "flux1-dev-fp8.safetensors"
                    }
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "batch_size": 1,
                        "height": 256,
                        "width": 256
                    }
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "simple test image"
                    }
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "clip": ["4", 1],
                        "text": "bad quality"
                    }
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    }
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": "test",
                        "images": ["8", 0]
                    }
                }
            }
        }
    
    async def test_health(self) -> bool:
        """Test server health status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        health = await response.json()
                        return health.get('status') == 'healthy'
            return False
        except Exception:
            return False
    
    async def run_single_test(self, prompt_name: str, prompt: Dict[str, Any], 
                             test_id: int, session: aiohttp.ClientSession) -> TestResult:
        """Run single test"""
        client_id = f"benchmark_{test_id}_{int(time.time())}"
        
        data = {
            "prompt": prompt,
            "client_id": client_id
        }
        
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/prompt_sync",
                json=data,
                timeout=aiohttp.ClientTimeout(total=600)  # 10 minutes timeout
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    return TestResult(
                        prompt_id=result.get('prompt_id', 'unknown'),
                        status=result.get('status', 'unknown'),
                        execution_time=result.get('execution_time', 0),
                        response_time=response_time,
                        success=True,
                        prompt_name=prompt_name,
                        test_id=test_id
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        prompt_id='unknown',
                        status='error',
                        execution_time=0,
                        response_time=response_time,
                        success=False,
                        prompt_name=prompt_name,
                        test_id=test_id,
                        error=f"HTTP {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            return TestResult(
                prompt_id='unknown',
                status='timeout',
                execution_time=0,
                response_time=time.time() - start_time,
                success=False,
                prompt_name=prompt_name,
                test_id=test_id,
                error="Request timeout"
            )
        except Exception as e:
            return TestResult(
                prompt_id='unknown',
                status='error',
                execution_time=0,
                response_time=time.time() - start_time,
                success=False,
                prompt_name=prompt_name,
                test_id=test_id,
                error=str(e)
            )
    
    async def run_benchmark(self, prompt_names: List[str], total_requests: int, 
                           concurrent_requests: int = 1) -> List[TestResult]:
        """Run benchmark test"""
        prompt_templates = self.get_prompt_templates()
        
        # Validate prompt names
        for name in prompt_names:
            if name not in prompt_templates:
                raise ValueError(f"Unknown prompt: {name}. Available: {list(prompt_templates.keys())}")
        
        print(f"Starting benchmark test...")
        print(f"  Server: {self.base_url}")
        print(f"  Prompts: {prompt_names}")
        print(f"  Total requests: {total_requests}")
        print(f"  Concurrent requests: {concurrent_requests}")
        print("-" * 60)
        
        # Health check
        print("Health check...")
        if not await self.test_health():
            print("ERROR: Server health check failed!")
            return []
        print("Server is healthy")
        
        # Generate prompts for testing
        print("Generating unique prompts for each request...")
        test_prompts = []
        requests_per_template = total_requests // len(prompt_names)
        remaining_requests = total_requests % len(prompt_names)
        
        for i, prompt_name in enumerate(prompt_names):
            count = requests_per_template
            if i < remaining_requests:
                count += 1
            
            prompts = self.generate_prompt_variations(prompt_name, count)
            for j, prompt in enumerate(prompts):
                test_prompts.append((prompt_name, prompt, len(test_prompts) + 1))
        
        print(f"Generated {len(test_prompts)} unique prompts")
        
        # Prepare test tasks
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def run_with_semaphore(prompt_name: str, prompt: Dict[str, Any], test_id: int, session: aiohttp.ClientSession):
            async with semaphore:
                return await self.run_single_test(prompt_name, prompt, test_id, session)
        
        # Execute tests
        async with aiohttp.ClientSession() as session:
            benchmark_start_time = time.time()
            
            tasks = []
            for prompt_name, prompt, test_id in test_prompts:
                task = run_with_semaphore(prompt_name, prompt, test_id, session)
                tasks.append(task)
            
            # Run all tasks and show progress
            results = []
            completed = 0
            
            for future in asyncio.as_completed(tasks):
                result = await future
                results.append(result)
                completed += 1
                
                # Show progress
                progress = (completed / total_requests) * 100
                status = "SUCCESS" if result.success else "FAILED"
                print(f"\rProgress: {completed}/{total_requests} ({progress:.1f}%) - "
                      f"Last: {status} ({result.execution_time:.1f}s)", end="", flush=True)
            
            benchmark_total_time = time.time() - benchmark_start_time
            print(f"\nBenchmark completed in {benchmark_total_time:.2f}s")
            
        return results
    
    def print_statistics(self, results: List[TestResult]):
        """Print test statistics"""
        if not results:
            print("ERROR: No results to analyze")
            return
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        print("\n" + "=" * 60)
        print("BENCHMARK STATISTICS")
        print("=" * 60)
        
        # Basic statistics
        total_requests = len(results)
        successful_count = len(successful_results)
        failed_count = len(failed_results)
        success_rate = (successful_count / total_requests) * 100
        
        print(f"Total Requests:      {total_requests}")
        print(f"Successful:          {successful_count} ({success_rate:.1f}%)")
        print(f"Failed:              {failed_count} ({(100-success_rate):.1f}%)")
        
        if successful_results:
            # Response time statistics
            response_times = [r.response_time for r in successful_results]
            execution_times = [r.execution_time for r in successful_results]
            
            print(f"\nRESPONSE TIME STATISTICS:")
            print(f"Average:             {mean(response_times):.2f}s")
            print(f"Median:              {median(response_times):.2f}s")
            print(f"Min:                 {min(response_times):.2f}s")
            print(f"Max:                 {max(response_times):.2f}s")
            print(f"Total Time:          {sum(response_times):.2f}s")
            
            print(f"\nEXECUTION TIME STATISTICS:")
            print(f"Average:             {mean(execution_times):.2f}s")
            print(f"Median:              {median(execution_times):.2f}s")
            print(f"Min:                 {min(execution_times):.2f}s")
            print(f"Max:                 {max(execution_times):.2f}s")
            print(f"Total Time:          {sum(execution_times):.2f}s")
            
            # Throughput calculations
            total_wall_time = max(response_times) if len(response_times) == 1 else sum(response_times)
            successful_throughput = successful_count / total_wall_time if total_wall_time > 0 else 0
            
            print(f"\nTHROUGHPUT ANALYSIS:")
            print(f"Requests/second:     {successful_throughput:.2f}")
            print(f"Avg req/sec:         {successful_count / mean(response_times):.2f}")
            
            # Prompt type breakdown
            print(f"\nPROMPT TYPE BREAKDOWN:")
            prompt_stats = {}
            for result in successful_results:
                name = result.prompt_name
                if name not in prompt_stats:
                    prompt_stats[name] = []
                prompt_stats[name].append(result.execution_time)
            
            for prompt_name, times in prompt_stats.items():
                avg_time = mean(times)
                count = len(times)
                print(f"  {prompt_name}: {count} requests, avg {avg_time:.2f}s")
        
        # Error analysis
        if failed_results:
            print(f"\nERROR ANALYSIS:")
            error_types = {}
            for result in failed_results:
                error_key = result.error.split(':')[0] if result.error else result.status
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            for error, count in error_types.items():
                print(f"  {error}: {count} times")
        
        print("=" * 60)


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="ComfyUI Worker Benchmark Tool")
    parser.add_argument(
        "--url", 
        default="https://7c277bc02703e41b-18188.af-za-1.gpu-instance.novita.ai",
        help="ComfyUI Worker server URL"
    )
    parser.add_argument(
        "--requests", "-n",
        type=int,
        default=10,
        help="Total number of requests (default: 10)"
    )
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=1,
        help="Number of concurrent requests (default: 1)"
    )
    parser.add_argument(
        "--prompts", "-p",
        nargs='+',
        default=["pretty_girl"],
        choices=["pretty_girl", "landscape", "fast_test"],
        help="Prompt templates to use (default: pretty_girl)"
    )
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompt templates"
    )
    
    args = parser.parse_args()
    
    benchmark = ComfyUIBenchmark(args.url)
    
    if args.list_prompts:
        print("Available prompt templates:")
        templates = benchmark.get_prompt_templates()
        for name, template in templates.items():
            positive_text = template["6"]["inputs"]["text"]
            steps = template["3"]["inputs"]["steps"]
            size = f"{template['5']['inputs']['width']}x{template['5']['inputs']['height']}"
            print(f"  {name}: '{positive_text}' ({steps} steps, {size})")
        return
    
    # Run benchmark test
    results = await benchmark.run_benchmark(
        prompt_names=args.prompts,
        total_requests=args.requests,
        concurrent_requests=args.concurrent
    )
    
    # Print statistics
    benchmark.print_statistics(results)


if __name__ == "__main__":
    asyncio.run(main()) 