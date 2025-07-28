# Docker Build Guide for ComfyUI Projects

This guide explains how to adapt existing ComfyUI projects to work with the ComfyUI Worker Handler for serverless deployment.

## 🎯 Overview

The ComfyUI Worker Handler can be integrated into existing ComfyUI projects to enable synchronous API access and serverless deployment. This document provides step-by-step instructions for building Docker images that include both ComfyUI and the Worker Handler.

## 📋 Prerequisites

- Existing ComfyUI project or setup
- Docker installed on your system
- Basic understanding of Docker concepts
- Access to ComfyUI models and custom nodes (if any)

## 🏗️ Adaptation Strategies

### Strategy 1: Integrate with Existing ComfyUI Project

Use this approach when you have an existing ComfyUI project that you want to make serverless-compatible.

### Strategy 2: Standalone Handler with External ComfyUI

Use this approach when you want to keep ComfyUI and the handler as separate services.

## 📁 Project Structure for Integration

```
your-comfyui-project/
├── ComfyUI/                     # Original ComfyUI installation
│   ├── main.py
│   ├── models/
│   ├── custom_nodes/
│   └── ...
├── worker-handler/              # ComfyUI Worker Handler
│   ├── server.py
│   ├── config.py
│   ├── comfyui/
│   └── requirements.txt
├── docker/                      # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── supervisord.conf
│   └── entrypoint.sh
├── models/                      # Model files (mounted or copied)
└── custom_nodes/               # Custom nodes (if any)
```

## 🐳 Dockerfile Examples

## 🔧 Build Scripts

```bash
# Basic build
./docker/build.sh

# Build with custom name and tag
IMAGE_NAME=my-comfyui-worker TAG=v1.0 ./docker/build.sh

# Build and push to registry
PUSH=true ./docker/build.sh

# Multi-platform build
PLATFORM=linux/amd64,linux/arm64 ./docker/build.sh
```

---

This guide provides comprehensive instructions for adapting existing ComfyUI projects to work with the Worker Handler. Choose the approach that best fits your project structure and deployment requirements. 