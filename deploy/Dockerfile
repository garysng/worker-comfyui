FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1


# install system packages and supervisor
RUN apt update -y && apt install -y \
        python3 python-is-python3 python3-pip \
        git aria2 curl netcat lsof supervisor && \
    apt clean

RUN cd /root && git clone https://github.com/comfyanonymous/ComfyUI && \
    cd ComfyUI && pip install -r requirements.txt
RUN cd /root/ComfyUI/models/checkpoints/ && aria2c -k 1M -s 10 -x 10 https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors -o flux1-dev-fp8.safetensors
# Copy comfyui-sync-handler project
COPY . /app/comfyui-sync-handler
WORKDIR /app/comfyui-sync-handler
RUN pip install -r requirements.txt

# Copy supervisor configuration and entrypoint
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh

# Make scripts executable
RUN chmod +x start.sh /usr/local/bin/entrypoint.sh

# Set environment variables for ComfyUI server configuration
ENV COMFYUI_SERVER_HOST=0.0.0.0
ENV COMFYUI_SERVER_PORT=8188
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=18188
ENV DEFAULT_TIMEOUT=600
ENV LOG_LEVEL=INFO

# Expose ports
EXPOSE 8188 18188

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:18188/health || exit 1

CMD ["/usr/local/bin/entrypoint.sh", "supervisord"]
