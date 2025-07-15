# Ollama STT App - GPU and Docker Support

## New Features

### 🎮 GPU Detection and Support

The app now automatically detects your GPU configuration and selects the optimal runtime:

1. **CUDA Support**: If you have an NVIDIA GPU with CUDA installed, it will use CUDA for maximum performance
2. **Studio Drivers**: Falls back to NVIDIA Studio drivers if CUDA is not available
3. **Gaming Drivers**: Uses standard NVIDIA gaming drivers as another fallback
4. **CPU Fallback**: Runs on CPU if no GPU acceleration is available

### 🔍 GPU Information

Check your GPU configuration:

```bash
python ollama_stt_simple.py --gpu_info
```

### 🎯 Runtime Selection

You can manually specify the runtime:

```bash
# Force CPU runtime
python ollama_stt_simple.py --runtime cpu

# Force CUDA runtime
python ollama_stt_simple.py --runtime cuda

# Force NVIDIA Studio runtime
python ollama_stt_simple.py --runtime nvidia-studio

# Force NVIDIA Gaming runtime
python ollama_stt_simple.py --runtime nvidia-gaming

# Auto-detect (default)
python ollama_stt_simple.py --runtime auto
```

### 🐳 Docker Support

Run the entire application in a Docker container for consistent behavior across different systems.

#### Quick Start with Docker

**Windows:**
```cmd
# Run with batch file (recommended)
run_docker.bat

# Or run manually
python ollama_stt_simple.py --docker
```

**Linux/macOS:**
```bash
# Run with Docker flag
python ollama_stt_simple.py --docker

# Or build and run manually
docker build -t ollama-stt .
docker run --rm -it -v "./transcriptions:/app/transcriptions" ollama-stt
```

#### Docker with GPU Support

If you have NVIDIA GPU with Docker GPU support:

```bash
# The app will automatically detect and use GPU in Docker
python ollama_stt_simple.py --docker --runtime cuda
```

#### Docker Compose

The app automatically generates a `docker-compose.yml` file:

```bash
# Build and run with docker-compose
docker-compose up --build
```

### 📝 New Command Line Options

- `--docker`: Run in Docker container
- `--runtime`: Specify runtime (auto, cpu, cuda, nvidia-studio, nvidia-gaming)
- `--gpu_info`: Show GPU information and exit

### 🛠️ Technical Details

#### GPU Detection Process

1. **NVIDIA GPU Check**: Uses `nvidia-smi` to detect NVIDIA GPUs
2. **CUDA Availability**: Checks for CUDA support
3. **Driver Type Detection**: Attempts to identify Studio vs Gaming drivers
4. **Fallback Chain**: CUDA → Studio → Gaming → CPU

#### Docker Container Features

- **Multi-stage build**: Optimized for both GPU and CPU scenarios
- **Audio system setup**: Configures PulseAudio for container audio
- **Volume mounts**: Persistent storage for transcriptions
- **Environment variables**: Proper Python and audio configuration
- **GPU passthrough**: Automatic GPU device mounting when available

#### Requirements

**For GPU support:**
- NVIDIA GPU with appropriate drivers
- CUDA toolkit (for CUDA runtime)
- `nvidia-smi` command available

**For Docker support:**
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Docker Compose (optional, for compose workflow)

### 🚀 Performance Optimization

The app automatically selects the best available runtime:

1. **CUDA**: Fastest for NVIDIA GPUs with CUDA
2. **Studio Drivers**: Optimized for content creation workloads
3. **Gaming Drivers**: Standard gaming performance
4. **CPU**: Compatible with all systems

### 🔧 Troubleshooting

#### GPU Issues

```bash
# Check GPU info
python ollama_stt_simple.py --gpu_info

# Force CPU if GPU issues
python ollama_stt_simple.py --runtime cpu
```

#### Docker Issues

```bash
# Check Docker status
docker --version
docker ps

# Force rebuild
docker build --no-cache -t ollama-stt .
```

#### Audio in Docker

Audio in Docker containers can be complex. The app includes:
- PulseAudio configuration
- Audio device mounting
- Environment variable setup

For Windows Docker Desktop, audio passthrough may have limitations.

### 📋 Examples

**Basic usage with auto GPU detection:**
```bash
python ollama_stt_simple.py --duration 10
```

**Run in Docker with specific runtime:**
```bash
python ollama_stt_simple.py --docker --runtime cuda --duration 10
```

**Check system capabilities:**
```bash
python ollama_stt_simple.py --gpu_info
```

**Run with custom TTS forwarding:**
```bash
python ollama_stt_simple.py --docker --voice female_us --model llama3.1:latest
```
