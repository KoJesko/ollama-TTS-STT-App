#!/bin/bash

# Docker entrypoint script for Ollama STT App

# Setup audio system for Docker
if [ ! -d "/tmp/pulse-runtime" ]; then
    mkdir -p /tmp/pulse-runtime
fi

# Start PulseAudio in the background if not running
if ! pgrep -x "pulseaudio" > /dev/null; then
    echo "Starting PulseAudio..."
    pulseaudio --start --log-target=syslog --system=false &
    sleep 2
fi

# Set up environment variables
export PULSE_SERVER=unix:/tmp/pulse-runtime/pulse/native
export PULSE_RUNTIME_PATH=/tmp/pulse-runtime

# Check for GPU support
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected in container"
    nvidia-smi --query-gpu=name --format=csv,noheader
else
    echo "🖥️  Running on CPU"
fi

# Run the Python script with all passed arguments
if [ $# -eq 0 ]; then
    # Default to web portal if no arguments provided
    exec python /app/web_portal.py
else
    # Otherwise run with provided arguments
    exec "$@"
fi
