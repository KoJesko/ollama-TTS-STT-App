# Ollama STT Docker Setup Guide

## 🐳 Quick Start

The easiest way to run the Ollama STT application is using Docker. The containerized version provides a consistent environment and eliminates dependency issues.

### Prerequisites

- Docker Desktop installed and running
- Git (to clone the repository)

### Running the Application

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd ollama-stt
   ```

2. **Run the Docker container**:
   ```bash
   # Windows
   .\run_docker.bat
   
   # Linux/macOS
   ./run_docker.sh
   ```

3. **Access the web interface**:
   Open your browser and navigate to: `http://localhost:55667`

The application will:
- 📦 Automatically install all dependencies
- 🎙️ Provide a web interface for speech-to-text conversion
- 💾 Save transcriptions to the `transcriptions/` folder
- 🔄 Forward text to TTS if needed

## 📁 Project Structure

```
ollama-stt/
├── Dockerfile              # Docker container configuration
├── run_docker.bat          # Windows Docker launcher
├── entrypoint.sh           # Container startup script
├── requirements.txt        # Python dependencies
├── web_portal.py          # Main web application
├── ollama_stt_app.py      # STT application
├── ollama_tts_app.py      # TTS application
├── templates/             # Web interface templates
├── transcriptions/        # Output folder (mounted as volume)
├── uploads/              # Upload folder (mounted as volume)
└── models/               # Ollama models storage
```

## 🔧 Docker Configuration

### Dockerfile Features

- **Base Image**: Python 3.11 slim for optimal size
- **System Dependencies**: Audio libraries (portaudio19-dev, alsa-utils)
- **Python Dependencies**: All requirements from requirements.txt
- **Volume Mounts**: Persistent storage for transcriptions and uploads
- **Port Exposure**: Port 55667 for web interface
- **Entrypoint**: Flexible startup script

### Volume Mounts

The Docker container mounts these local directories:
- `./transcriptions` → `/app/transcriptions` (transcription outputs)
- `./uploads` → `/app/uploads` (file uploads)

### Port Mapping

- **Container Port**: 55667
- **Host Port**: 55667
- **Protocol**: HTTP

## 🚀 Manual Docker Commands

If you prefer to run Docker commands manually:

### Build the Image
```bash
docker build -t ollama-stt .
```

### Run the Container
```bash
docker run --rm -it \
  -p 55667:55667 \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  -v "$(pwd)/uploads:/app/uploads" \
  ollama-stt
```

### Run with Custom Arguments
```bash
# Run a specific script
docker run --rm -it ollama-stt python ollama_stt_app.py --help

# Run with environment variables
docker run --rm -it \
  -p 55667:55667 \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  -v "$(pwd)/uploads:/app/uploads" \
  ollama-stt
```

## 🛠️ Development Mode

For development, you can mount the source code as a volume:

```bash
docker run --rm -it \
  -p 55667:55667 \
  -v "$(pwd):/app" \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  -v "$(pwd)/uploads:/app/uploads" \
  ollama-stt
```

## 🎯 Advanced Features

### GPU Support (NVIDIA)

To use GPU acceleration with NVIDIA cards:

```bash
docker run --rm -it \
  --gpus all \
  -p 55667:55667 \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  -v "$(pwd)/uploads:/app/uploads" \
  ollama-stt
```

### Custom Ollama Host

If Ollama is running on a different host:

```bash
docker run --rm -it \
  -p 55667:55667 \
  -e OLLAMA_HOST=192.168.1.100:11434 \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  -v "$(pwd)/uploads:/app/uploads" \
  ollama-stt
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 55667
   netstat -tulpn | grep 55667
   
   # Use a different port
   docker run --rm -it -p 8080:55667 ollama-stt
   ```

2. **Docker Build Fails**
   ```bash
   # Clean up Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker build --no-cache -t ollama-stt .
   ```

3. **Permission Issues (Linux/macOS)**
   ```bash
   # Fix permissions for transcriptions folder
   sudo chown -R $USER:$USER transcriptions/
   ```

4. **Audio Device Issues**
   - Audio warnings in Docker are normal
   - The web interface handles audio through the browser
   - File upload functionality works regardless of audio device status

### Logs and Debugging

```bash
# View container logs
docker logs <container-id>

# Run with debug mode
docker run --rm -it \
  -p 55667:55667 \
  -e FLASK_DEBUG=1 \
  ollama-stt
```

## 📊 Performance Notes

- **First Run**: Takes longer due to dependency installation
- **Subsequent Runs**: Fast startup using cached layers
- **Memory Usage**: ~500MB-1GB depending on models loaded
- **CPU Usage**: Minimal when idle, increases during transcription

## 🔒 Security Considerations

- The container runs with non-root user where possible
- No sensitive data is stored in the container
- All data persists in mounted volumes
- Web interface is bound to localhost by default

## 📝 Next Steps

1. **Access the Web Interface**: Open `http://localhost:55667`
2. **Upload Audio Files**: Use the web interface to upload audio files
3. **Configure Ollama**: Set up Ollama models for TTS functionality
4. **Customize Settings**: Modify configuration through the web interface

## 🆘 Support

If you encounter issues:

1. Check the Docker logs
2. Verify Docker Desktop is running
3. Ensure no other applications are using port 55667
4. Review the troubleshooting section above

For more advanced usage, see the `GPU_DOCKER_README.md` file.
