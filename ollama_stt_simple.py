import argparse
import sys
import subprocess
import importlib.util
from datetime import datetime
import os
import time
import platform
import json
import re

def install_package(package_name):
    """Install a package using pip."""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {e}", file=sys.stderr)
        return False

def check_and_install_dependencies():
    """Check for required packages and install them if missing."""
    required_packages = {
        'speech_recognition': 'SpeechRecognition',
        'pyaudio': 'pyaudio',
        'pydub': 'pydub',
        'yaml': 'PyYAML'
    }
    
    packages_to_install = []
    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            packages_to_install.append((module_name, package_name))
    
    if packages_to_install:
        print("Installing required packages...")
        for module_name, package_name in packages_to_install:
            print(f"Package '{module_name}' not found. Installing...")
            if not install_package(package_name):
                print(f"Failed to install {package_name}. Please install manually.", file=sys.stderr)
                if module_name == 'pyaudio':
                    print("For PyAudio on Windows, try: pip install --upgrade pip setuptools wheel", file=sys.stderr)
                    print("Then: pip install pyaudio", file=sys.stderr)
                sys.exit(1)
    
    # Try to import the packages
    try:
        import speech_recognition as sr
        try:
            import pyaudio
        except ImportError:
            print("PyAudio import failed. Some microphone features may not work.", file=sys.stderr)
            pyaudio = None
        
        try:
            from pydub import AudioSegment
        except ImportError:
            print("Pydub import failed. Some audio processing features may not work.", file=sys.stderr)
            AudioSegment = None
        
        try:
            import yaml
        except ImportError:
            print("PyYAML import failed. Docker support may not work.", file=sys.stderr)
            yaml = None
        
        return sr, pyaudio, AudioSegment
    except ImportError as e:
        print(f"Critical import error: {e}", file=sys.stderr)
        sys.exit(1)

def record_audio_simple(duration=5):
    """Simple audio recording for a fixed duration."""
    sr, pyaudio_module, _ = check_and_install_dependencies()
    
    if pyaudio_module is None:
        print("PyAudio not available. Cannot record audio.", file=sys.stderr)
        return None
    
    recognizer = sr.Recognizer()
    
    try:
        microphone = sr.Microphone()
    except Exception as e:
        print(f"Error initializing microphone: {e}", file=sys.stderr)
        print("Please check if a microphone is connected and accessible.", file=sys.stderr)
        return None
    
    print("🎤 Adjusting for ambient noise... Please wait.")
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception as e:
        print(f"Warning: Could not adjust for ambient noise: {e}")
    
    print(f"🔴 Recording for {duration} seconds. Speak now!")
    try:
        with microphone as source:
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
        print("🔴 Recording stopped.")
        return audio
    except Exception as e:
        print(f"Error during recording: {e}", file=sys.stderr)
        return None

def transcribe_audio(audio, engine="google"):
    """Transcribe audio data to text using specified engine."""
    if audio is None:
        print("No audio data to transcribe.", file=sys.stderr)
        return ""
    
    sr, _, _ = check_and_install_dependencies()
    recognizer = sr.Recognizer()
    
    print(f"🔤 Transcribing audio using {engine}...")
    
    try:
        if engine == "google":
            text = recognizer.recognize_google(audio)
        elif engine == "whisper":
            try:
                text = recognizer.recognize_whisper(audio)
            except sr.RequestError:
                print("Whisper not available, falling back to Google...")
                text = recognizer.recognize_google(audio)
        else:
            text = recognizer.recognize_google(audio)  # fallback
        
        print(f"📝 Transcribed: {text}")
        return text.strip()
        
    except sr.UnknownValueError:
        print("⚠️  Could not understand the audio")
        return ""
    except sr.RequestError as e:
        print(f"❌ Error with {engine} service: {e}")
        # Try offline recognition as fallback
        try:
            print("Trying offline recognition...")
            text = recognizer.recognize_sphinx(audio)
            print(f"📝 Transcribed (offline): {text}")
            return text.strip()
        except:
            print("⚠️  Offline recognition also failed")
            return ""
    except Exception as e:
        print(f"❌ Unexpected error during transcription: {e}")
        return ""

def save_transcription(text, output_path=None):
    """Save transcription to a file."""
    if not text.strip():
        return None
        
    if not output_path:
        documents_path = os.path.expanduser("~/Documents")
        stt_history_path = os.path.join(documents_path, "SchmidtSims", "STTHistory")
        os.makedirs(stt_history_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(stt_history_path, f"stt_output_{timestamp}.txt")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"💾 Transcription saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving transcription: {e}")
        return None

def forward_to_tts(text, tts_script_path, voice=None, model=None, verbose=False):
    """Forward the transcribed text to the TTS script."""
    if not text.strip():
        print("No text to forward to TTS.", file=sys.stderr)
        return
    
    print(f"🔄 Forwarding to TTS: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    # Construct command for TTS script
    cmd = [sys.executable, tts_script_path, text]
    
    if voice:
        cmd.extend(["--voice", voice])
    if model:
        cmd.extend(["--model", model])
    if verbose:
        cmd.append("--verbose")
    
    try:
        # Run the TTS script
        print("🔄 Running TTS script...")
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ TTS completed successfully!")
        else:
            print(f"❌ TTS failed with return code: {result.returncode}")
    except Exception as e:
        print(f"❌ Error running TTS script: {e}")

def detect_gpu_support():
    """Detect GPU support and return the best available option."""
    gpu_info = {
        'has_nvidia': False,
        'has_cuda': False,
        'has_studio_drivers': False,
        'has_gaming_drivers': False,
        'recommended_runtime': 'cpu'
    }
    
    print("🔍 Detecting GPU support...")
    
    # Check for NVIDIA GPU
    try:
        # Try nvidia-smi command
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            gpu_info['has_nvidia'] = True
            print(f"✅ NVIDIA GPU detected: {result.stdout.strip()}")
            
            # Check for CUDA
            try:
                cuda_result = subprocess.run(['nvidia-smi', '--query-gpu=cuda_version', '--format=csv,noheader'], 
                                           capture_output=True, text=True, timeout=10)
                if cuda_result.returncode == 0 and cuda_result.stdout.strip() and cuda_result.stdout.strip() != 'N/A':
                    gpu_info['has_cuda'] = True
                    gpu_info['recommended_runtime'] = 'cuda'
                    print(f"✅ CUDA support detected: {cuda_result.stdout.strip()}")
            except:
                pass
            
            # Check driver type by version pattern
            driver_version = result.stdout.strip().split(',')[1].strip() if ',' in result.stdout else ''
            if driver_version:
                # Studio drivers typically have different version patterns
                # This is a heuristic - actual detection would require more sophisticated methods
                if 'studio' in driver_version.lower():
                    gpu_info['has_studio_drivers'] = True
                    if not gpu_info['has_cuda']:
                        gpu_info['recommended_runtime'] = 'nvidia-studio'
                else:
                    gpu_info['has_gaming_drivers'] = True
                    if not gpu_info['has_cuda']:
                        gpu_info['recommended_runtime'] = 'nvidia-gaming'
            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        print("ℹ️  No NVIDIA GPU detected or nvidia-smi not available")
    
    # Check for other GPU types (AMD, Intel)
    try:
        if platform.system() == "Windows":
            # Check Windows GPU info
            wmic_result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                       capture_output=True, text=True, timeout=10)
            if wmic_result.returncode == 0:
                gpu_names = wmic_result.stdout.lower()
                if 'amd' in gpu_names or 'radeon' in gpu_names:
                    print("ℹ️  AMD GPU detected (CPU runtime recommended)")
                elif 'intel' in gpu_names:
                    print("ℹ️  Intel GPU detected (CPU runtime recommended)")
    except:
        pass
    
    print(f"🎯 Recommended runtime: {gpu_info['recommended_runtime']}")
    return gpu_info

def check_docker_support():
    """Check if Docker is available and running."""
    docker_info = {
        'available': False,
        'running': False,
        'version': None
    }
    
    try:
        # Check if Docker is installed
        version_result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
        if version_result.returncode == 0:
            docker_info['available'] = True
            docker_info['version'] = version_result.stdout.strip()
            print(f"✅ Docker available: {docker_info['version']}")
            
            # Check if Docker daemon is running
            try:
                ps_result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
                if ps_result.returncode == 0:
                    docker_info['running'] = True
                    print("✅ Docker daemon is running")
                else:
                    print("⚠️  Docker is installed but daemon is not running")
            except:
                print("⚠️  Cannot check Docker daemon status")
        else:
            print("ℹ️  Docker not found")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        print("ℹ️  Docker not available")
    
    return docker_info

def create_dockerfile(gpu_info):
    """Create a Dockerfile based on GPU capabilities."""
    if gpu_info['has_cuda']:
        base_image = "nvidia/cuda:11.8-runtime-ubuntu22.04"
        runtime_args = ["--gpus", "all"]
    else:
        base_image = "python:3.9-slim"
        runtime_args = []
    
    dockerfile_content = f"""FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    portaudio19-dev \\
    python3-pyaudio \\
    ffmpeg \\
    alsa-utils \\
    pulseaudio \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/transcriptions /app/uploads

# Expose port if needed
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PULSE_RUNTIME_PATH=/tmp/pulse-runtime

# Default command
CMD ["python", "ollama_stt_simple.py", "--help"]
"""
    
    return dockerfile_content, runtime_args

def create_docker_compose(gpu_info):
    """Create a docker-compose.yml file based on GPU capabilities."""
    compose_content = {
        'version': '3.8',
        'services': {
            'ollama-stt': {
                'build': '.',
                'volumes': [
                    './transcriptions:/app/transcriptions',
                    './uploads:/app/uploads'
                ],
                'environment': [
                    'PYTHONUNBUFFERED=1'
                ],
                'stdin_open': True,
                'tty': True
            }
        }
    }
    
    # Add GPU support if available
    if gpu_info['has_cuda']:
        compose_content['services']['ollama-stt']['deploy'] = {
            'resources': {
                'reservations': {
                    'devices': [{
                        'driver': 'nvidia',
                        'count': 'all',
                        'capabilities': ['gpu']
                    }]
                }
            }
        }
    
    return compose_content

def run_in_docker(args, gpu_info, docker_info):
    """Run the application in Docker."""
    if not docker_info['running']:
        print("❌ Docker daemon is not running. Please start Docker Desktop.")
        return False
    
    print("🐳 Setting up Docker environment...")
    
    # Create Dockerfile
    dockerfile_content, runtime_args = create_dockerfile(gpu_info)
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("📝 Created Dockerfile")
    
    # Create docker-compose.yml
    compose_config = create_docker_compose(gpu_info)
    import yaml
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(compose_config, f, default_flow_style=False)
    print("📝 Created docker-compose.yml")
    
    # Build the Docker image
    print("🔨 Building Docker image...")
    build_cmd = ['docker', 'build', '-t', 'ollama-stt', '.']
    build_result = subprocess.run(build_cmd, capture_output=False)
    
    if build_result.returncode != 0:
        print("❌ Docker build failed")
        return False
    
    # Prepare Docker run command
    docker_cmd = ['docker', 'run', '--rm', '-it']
    docker_cmd.extend(runtime_args)
    
    # Mount volumes
    docker_cmd.extend(['-v', f'{os.getcwd()}/transcriptions:/app/transcriptions'])
    docker_cmd.extend(['-v', f'{os.getcwd()}/uploads:/app/uploads'])
    
    # Add audio device access (Linux/macOS)
    if platform.system() != "Windows":
        docker_cmd.extend(['--device', '/dev/snd'])
    
    # Add the image name
    docker_cmd.append('ollama-stt')
    
    # Add application arguments
    app_args = []
    if args.duration != 5:
        app_args.extend(['--duration', str(args.duration)])
    if args.engine != 'google':
        app_args.extend(['--engine', args.engine])
    if args.output_path:
        app_args.extend(['--output_path', args.output_path])
    if args.voice:
        app_args.extend(['--voice', args.voice])
    if args.model != 'llama3.1:latest':
        app_args.extend(['--model', args.model])
    if args.verbose:
        app_args.append('--verbose')
    if args.no_forward:
        app_args.append('--no_forward')
    
    docker_cmd.extend(app_args)
    
    print(f"🚀 Running in Docker: {' '.join(docker_cmd)}")
    
    try:
        result = subprocess.run(docker_cmd, capture_output=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n🛑 Docker execution interrupted by user.")
        return False
    except Exception as e:
        print(f"❌ Error running Docker container: {e}")
        return False

def main():
    print("🎙️  Ollama STT App - Starting up...")
    print("Checking dependencies...")
    
    parser = argparse.ArgumentParser(description="Record speech, convert to text, and forward to Ollama TTS.")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds (default: 5)")
    parser.add_argument("--engine", type=str, default="google", choices=["google", "whisper"], help="Speech recognition engine")
    parser.add_argument("--output_path", type=str, help="Optional. Path to save the transcription text file.")
    parser.add_argument("--tts_script", type=str, default="ollama_tts_app.py", help="Path to TTS script (default: ollama_tts_app.py)")
    parser.add_argument("--voice", type=str, help="Voice to use for TTS (e.g., female_us, male_uk)")
    parser.add_argument("--model", type=str, default="llama3.1:latest", help="Ollama model to use for TTS")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--no_forward", action="store_true", help="Don't forward to TTS, just transcribe")
    parser.add_argument("--docker", action="store_true", help="Run in Docker container")
    parser.add_argument("--runtime", type=str, choices=["auto", "cpu", "cuda", "nvidia-studio", "nvidia-gaming"], 
                       default="auto", help="Runtime to use (default: auto)")
    parser.add_argument("--gpu_info", action="store_true", help="Show GPU information and exit")
    
    args = parser.parse_args()
    
    # Detect GPU and Docker support
    gpu_info = detect_gpu_support()
    docker_info = check_docker_support()
    
    # Show GPU info if requested
    if args.gpu_info:
        print("\n🖥️  GPU Information:")
        print(f"  NVIDIA GPU: {'✅' if gpu_info['has_nvidia'] else '❌'}")
        print(f"  CUDA Support: {'✅' if gpu_info['has_cuda'] else '❌'}")
        print(f"  Studio Drivers: {'✅' if gpu_info['has_studio_drivers'] else '❌'}")
        print(f"  Gaming Drivers: {'✅' if gpu_info['has_gaming_drivers'] else '❌'}")
        print(f"  Recommended Runtime: {gpu_info['recommended_runtime']}")
        print(f"\n🐳 Docker Support:")
        print(f"  Available: {'✅' if docker_info['available'] else '❌'}")
        print(f"  Running: {'✅' if docker_info['running'] else '❌'}")
        if docker_info['version']:
            print(f"  Version: {docker_info['version']}")
        return
    
    # Override runtime if specified
    if args.runtime != "auto":
        gpu_info['recommended_runtime'] = args.runtime
        print(f"🎯 Using specified runtime: {args.runtime}")
    
    # Run in Docker if requested
    if args.docker:
        if not docker_info['available']:
            print("❌ Docker is not available. Please install Docker Desktop.")
            return
        
        success = run_in_docker(args, gpu_info, docker_info)
        if not success:
            print("❌ Docker execution failed.")
        return
    
    # Check dependencies early
    try:
        check_and_install_dependencies()
    except SystemExit:
        return
    
    # Check if TTS script exists
    tts_script_path = args.tts_script
    if not os.path.isabs(tts_script_path):
        # Make it relative to current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tts_script_path = os.path.join(script_dir, tts_script_path)
    
    if not args.no_forward and not os.path.exists(tts_script_path):
        print(f"❌ TTS script not found: {tts_script_path}", file=sys.stderr)
        print("Use --no_forward to skip TTS forwarding, or provide correct --tts_script path", file=sys.stderr)
        return
    
    # Show runtime information
    print(f"🏃 Running with {gpu_info['recommended_runtime']} runtime")
    
    try:
        # Record audio
        audio = record_audio_simple(args.duration)
        
        if audio is None:
            print("❌ Failed to record audio.")
            return
        
        # Transcribe audio
        transcribed_text = transcribe_audio(audio, args.engine)
        
        if transcribed_text:
            print(f"\n📝 Final Transcription: {transcribed_text}")
            
            # Save transcription
            save_transcription(transcribed_text, args.output_path)
            
            # Forward to TTS if requested
            if not args.no_forward:
                forward_to_tts(transcribed_text, tts_script_path, args.voice, args.model, args.verbose)
        else:
            print("❌ No speech detected or transcription failed.")
            
    except KeyboardInterrupt:
        print("\n🛑 Recording interrupted by user.")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
