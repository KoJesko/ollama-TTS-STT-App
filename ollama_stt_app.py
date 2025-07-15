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
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {e}", file=sys.stderr)
        sys.exit(1)

def check_and_install_dependencies():
    """Check for required packages and install them if missing."""
    required_packages = {
        'speech_recognition': 'SpeechRecognition',
        'pyaudio': 'pyaudio'
    }
    
    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"Package '{module_name}' not found. Installing...")
            install_package(package_name)

# Check and install dependencies first
check_and_install_dependencies()

# Now import after installation
try:
    import speech_recognition as sr
    import pyaudio
except ImportError as e:
    print(f"Failed to import required packages: {e}", file=sys.stderr)
    print("Please run the script again or manually install the packages.", file=sys.stderr)
    sys.exit(1)

def record_audio_until_silence(max_duration=60, silence_threshold=2.0):
    """Record audio until silence is detected or max duration is reached."""
    recognizer = sr.Recognizer()
    
    try:
        microphone = sr.Microphone()
    except Exception as e:
        print(f"Error initializing microphone: {e}", file=sys.stderr)
        return None
    
    print("🎤 Adjusting for ambient noise... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    print(f"🔴 Recording started. Speak now! (Max {max_duration} seconds, stops after {silence_threshold}s of silence)")
    
    audio_chunks = []
    start_time = time.time()
    last_audio_time = start_time
    
    try:
        with microphone as source:
            while True:
                current_time = time.time()
                
                # Check if max duration reached
                if current_time - start_time >= max_duration:
                    print(f"🔴 Maximum duration ({max_duration}s) reached. Stopping recording.")
                    break
                
                try:
                    # Listen for audio with a short timeout
                    audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=1)
                    audio_chunks.append(audio)
                    last_audio_time = current_time
                    print("🎵", end="", flush=True)  # Visual feedback for audio detection
                    
                except sr.WaitTimeoutError:
                    # No audio detected in this chunk
                    silence_duration = current_time - last_audio_time
                    if silence_duration >= silence_threshold:
                        print(f"\n🔇 {silence_threshold}s of silence detected. Stopping recording.")
                        break
                    print(".", end="", flush=True)  # Visual feedback for silence
                    
        print("\n🔴 Recording stopped.")
        
        # Combine all audio chunks into one
        if audio_chunks:
            # For simplicity, we'll return the first chunk
            # In a more advanced implementation, you'd combine them
            return audio_chunks[0] if len(audio_chunks) == 1 else audio_chunks[-1]
        else:
            return None
            
    except Exception as e:
        print(f"Error during recording: {e}", file=sys.stderr)
        return None

def transcribe_audio(audio, engine="google"):
    """Transcribe audio data to text using specified engine."""
    if audio is None:
        print("No audio data to transcribe.", file=sys.stderr)
        return ""
    
    recognizer = sr.Recognizer()
    
    print(f"🔤 Transcribing audio using {engine}...")
    
    try:
        if engine == "google":
            text = recognizer.recognize_google(audio)
        elif engine == "whisper":
            text = recognizer.recognize_whisper(audio)
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
    if not output_path:
        documents_path = os.path.expanduser("~/Documents")
        stt_history_path = os.path.join(documents_path, "SchmidtSims", "STTHistory")
        os.makedirs(stt_history_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(stt_history_path, f"stt_output_{timestamp}.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"💾 Transcription saved to: {output_path}")
    return output_path

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
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ TTS completed successfully!")
            if result.stdout:
                print("TTS Output:")
                print(result.stdout)
        else:
            print(f"❌ TTS failed with error:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running TTS script: {e}")

def main():
    print("🎙️  Ollama STT App - Starting up...")
    print("Checking dependencies...")
    
    parser = argparse.ArgumentParser(description="Record speech, convert to text, and forward to Ollama TTS.")
    parser.add_argument("--max_duration", type=int, default=60, help="Maximum recording duration in seconds (default: 60)")
    parser.add_argument("--silence_threshold", type=float, default=2.0, help="Seconds of silence before stopping (default: 2.0)")
    parser.add_argument("--engine", type=str, default="google", choices=["google", "whisper"], help="Speech recognition engine")
    parser.add_argument("--output_path", type=str, help="Optional. Path to save the transcription text file.")
    parser.add_argument("--tts_script", type=str, default="ollama_tts_app.py", help="Path to TTS script (default: ollama_tts_app.py)")
    parser.add_argument("--voice", type=str, help="Voice to use for TTS (e.g., female_us, male_uk)")
    parser.add_argument("--model", type=str, default="llama3.1:latest", help="Ollama model to use for TTS")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--no_forward", action="store_true", help="Don't forward to TTS, just transcribe")
    
    args = parser.parse_args()
    
    # Check if TTS script exists
    tts_script_path = args.tts_script
    if not os.path.isabs(tts_script_path):
        # Make it relative to current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tts_script_path = os.path.join(script_dir, tts_script_path)
    
    if not args.no_forward and not os.path.exists(tts_script_path):
        print(f"❌ TTS script not found: {tts_script_path}", file=sys.stderr)
        print("Use --no_forward to skip TTS forwarding, or provide correct --tts_script path", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Record audio
        audio = record_audio_until_silence(args.max_duration, args.silence_threshold)
        
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
        sys.exit(1)

if __name__ == "__main__":
    main()
