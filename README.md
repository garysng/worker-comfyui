# ComfyUI Worker for Serverless

A synchronous ComfyUI wrapper designed for serverless environments, enabling automatic scaling and efficient resource management on platforms like Novita.ai.

## 🎯 Project Overview

This project transforms the traditional asynchronous ComfyUI workflow into a synchronous HTTP API service, making it compatible with serverless platforms that require request-response patterns for automatic scaling.

### Key Features

- **🔄 Synchronous API**: Converts ComfyUI's async HTTP API to sync HTTP REST endpoints
- **📈 Auto-scaling Ready**: Compatible with serverless platforms for automatic resource scaling  
- **⚡ High Performance**: Optimized for fast startup and efficient processing
- **🐳 Docker Ready**: Pre-built containers for easy deployment
- **🔍 Health Monitoring**: Built-in health checks and monitoring endpoints
- **📊 Metrics & Logging**: Comprehensive logging and execution time tracking

## 🏗️ Architecture

```
┌─────────────────┐                ┌─────────────────────────────────┐
│   Client App    │   HTTP/REST    │        Serverless Platform      │
│                 │ ──────────────►│         (Novita.ai)             │
│ • Web Apps      │                │                                 │
│ • Mobile Apps   │                │ • Load Balancing                │
│ • API Clients   │                │ • Auto-scaling                  │
│                 │                │ • Health Monitoring             │
└─────────────────┘                │ • Request Routing               │
                                   └─────────────┬───────────────────┘
                                                 │ Container
                                                 │ Orchestration
                                                 ▼
                                   ┌───────────────────────────────────┐                ┌─────────────────┐
                                   │         ComfyUI Worker            │   HTTP/REST    │    ComfyUI      │
                                   │                                   │ ──────────────►│    Server       │
                                   │  ┌─────────────────────────────┐  │                │                 │
                                   │  │      FastAPI Handler        │  │                │ • Workflow      │
                                   │  │   (server.py)               │  │                │   Engine        │
                                   │  │                             │  │                │ • Model         │
                                   │  │  ┌─────────────────────┐    │  │                │   Runtime       │
                                   │  │  │   ComfyUI Client    │    │  │                │ • Queue         │
                                   │  │  │   (client.py)       │ ───┼──┼────────────────┤   Manager       │
                                   │  │  │                     │    │  │                │                 │
                                   │  │  │ • HTTP Polling      │    │  │                └─────────────────┘
                                   │  │  │ • Task Monitoring   │    │  │
                                   │  │  │ • Result Collection │    │  │
                                   │  │  └─────────────────────┘    │  │
                                   │  └─────────────────────────────┘  │
                                   └───────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (for containerized deployment)
- ComfyUI server (or use our integrated setup)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/garysng/worker-comfyui.git
cd worker-comfyui
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start the handler server**
```bash
python server.py
```

4. **Test the API**
```bash
curl -X POST "https://0.0.0.0:18188/prompt_sync" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
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
          "seed": 1047100913978686,
          "steps": 60
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
    }
  }'
```

### Docker Deployment

```bash
# Build the image
docker build -f deploy/Dockerfile -t comfyui-worker .

# Run the container
docker run -p 18188:18188 comfyui-worker
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/prompt_sync` | POST | Submit prompt and wait for completion (synchronous) |
| `/prompt` | POST | Submit prompt asynchronously (ComfyUI compatible) |
| `/queue` | GET | Get current queue status |
| `/history` | GET | Get execution history |
| `/health` | GET | Health check endpoint |
| `/interrupt` | POST | Interrupt current execution |

### Response Format

```json
{
  "prompt_id": "12345-abcde-67890",
  "status": "success", 
  "execution_time": 15.23,
  "outputs": {
    "9": {
      "images": [
        {
          "filename": "ComfyUI_00001_.png",
          "subfolder": "",
          "type": "output"
        }
      ]
    }
  },
  "node_errors": {}
}
```

## 🔧 Configuration

Environment variables for customization:

```bash
# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=18188

# ComfyUI configuration  
COMFYUI_SERVER_ADDRESS=127.0.0.1:8188
DEFAULT_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_OUTPUT=console  # console, file, both
```

## 📚 Documentation

### Core Documentationw
- **[🔧 Handler Implementation](docs/handler-implementation.md)** - Technical details of the synchronous wrapper
- **[🐳 Docker Build Guide](docs/docker-build.md)** - How to adapt existing ComfyUI projects
- **[☁️ Novita.ai Serverless](docs/run-on-novita.md)** - Deployment guide for Novita.ai platform

### Tools & Examples
- **[📊 Benchmark Tool](docs/examples/benchmark.py)** - Performance testing and load analysis

## 🛠️ Use Cases

### Serverless Image Generation
Perfect for applications that need on-demand image generation with automatic scaling:
- **API Services**: REST API for image generation
- **Web Applications**: Direct integration with web frontends
- **Batch Processing**: Scale up for bulk image generation
- **Cost Optimization**: Pay only for actual usage

## 🔍 Monitoring & Debugging

### Health Checks
```bash
curl http://localhost:18188/health
```

### Queue Monitoring
```bash
curl http://localhost:18188/queue
```

### Execution History
```bash
curl http://localhost:18188/history
```

## 🧪 Testing & Benchmarking

### Performance Benchmarking
```bash
python benchmark.py --url "http://localhost:18188" --requests 10 --concurrent 2
```

## 🐛 Troubleshooting

### Common Issues

1. **Server not responding**
   - Check if ComfyUI server is running
   - Verify port configuration

2. **Out of memory errors**
   - Reduce concurrent requests
   - Use smaller models
   - Increase container memory limits

3. **Timeout errors**
   - Increase `DEFAULT_TIMEOUT` value
   - Optimize prompt complexity
   - Check server resources

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python server.py
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - The underlying image generation framework
- [Novita.ai](https://novita.ai/) - Serverless platform support

---

**Ready to scale your ComfyUI workflows? Deploy on serverless today! 🚀** 