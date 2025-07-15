import argparse
import sys
import subprocess
import importlib.util
from datetime import datetime
import os
import time

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
        'pydub': 'pydub'
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
    
    args = parser.parse_args()
    
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
