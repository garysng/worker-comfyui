#!/bin/bash

# ComfyUI Worker Container Entrypoint
# This script is used as the container entrypoint when using supervisord

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-flight checks
log_info "=== ComfyUI Worker Starting ==="
log_info "Container environment:"
log_info "  ComfyUI: ${COMFYUI_SERVER_HOST}:${COMFYUI_SERVER_PORT}"
log_info "  Handler: ${SERVER_HOST}:${SERVER_PORT}"
log_info "  Timeout: ${DEFAULT_TIMEOUT}s"
log_info "  Log Level: ${LOG_LEVEL}"

# Check if ComfyUI exists
if [ ! -d "/root/ComfyUI" ]; then
    log_error "ComfyUI directory not found at /root/ComfyUI"
    exit 1
fi

if [ ! -f "/root/ComfyUI/main.py" ]; then
    log_error "ComfyUI main.py not found"
    exit 1
fi

# Check if handler exists
if [ ! -f "/app/comfyui-sync-handler/server.py" ]; then
    log_error "Handler server.py not found"
    exit 1
fi

# Check if supervisord config exists
if [ ! -f "/etc/supervisor/conf.d/supervisord.conf" ]; then
    log_error "Supervisord configuration not found"
    exit 1
fi

log_info "Pre-flight checks passed"

# Handle different startup modes
case "${1:-supervisord}" in
    "supervisord"|"")
        log_info "Starting with supervisord (default)"
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
        ;;
    "comfyui")
        log_info "Starting ComfyUI only"
        cd /root/ComfyUI
        exec python main.py --listen "${COMFYUI_SERVER_HOST}" --port "${COMFYUI_SERVER_PORT}"
        ;;
    "handler")
        log_info "Starting Handler only"
        cd /app/comfyui-sync-handler
        exec python server.py
        ;;
    "bash"|"sh")
        log_info "Starting interactive shell"
        exec /bin/bash
        ;;
    *)
        log_info "Starting custom command: $*"
        exec "$@"
        ;;
esac 