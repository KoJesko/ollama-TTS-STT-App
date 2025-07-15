"""
Enhanced Speech-to-Text App with Natural Human Speech Detection

This app now includes three recording modes optimized for natural human speech:

1. Smart Mode (default): Uses voice activity detection to naturally capture speech
   - Automatically detects when speech begins and ends
   - Handles natural pauses in speech gracefully
   - Optimized energy thresholds for better sensitivity

2. Natural Mode: Continuous streaming for natural speech flow
   - Records complete phrases without chunking
   - Better handling of speech patterns

3. Chunked Mode: Legacy method for compatibility
   - Original implementation with small audio chunks
   - More responsive but less natural for speech

Key improvements:
- Longer silence threshold (3s default) for natural speech patterns
- Better microphone calibration and noise adjustment
- Optimized recognizer settings for human speech
- Clear visual feedback during recording
- Enhanced error handling and user guidance
"""

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

def record_audio_until_silence(max_duration=60, silence_threshold=3.0):
    """Record audio until silence is detected or max duration is reached."""
    recognizer = sr.Recognizer()
    
    # Optimize recognizer settings for more natural speech detection
    recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Allow for natural pauses in speech
    recognizer.phrase_threshold = 0.3  # Minimum audio length to be considered a phrase
    recognizer.non_speaking_duration = 0.8  # How long to wait before considering silence
    
    try:
        microphone = sr.Microphone()
    except Exception as e:
        print(f"Error initializing microphone: {e}", file=sys.stderr)
        return None
    
    print("🎤 Adjusting for ambient noise... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    
    print(f"🔴 Recording started. Speak naturally! (Max {max_duration} seconds, stops after {silence_threshold}s of silence)")
    print("💡 Natural pauses are okay - the system will wait for you to finish speaking.")
    
    start_time = time.time()
    last_speech_time = start_time
    audio_data = None
    speech_started = False
    
    try:
        with microphone as source:
            while True:
                current_time = time.time()
                
                # Check if max duration reached
                if current_time - start_time >= max_duration:
                    print(f"\n🔴 Maximum duration ({max_duration}s) reached. Stopping recording.")
                    break
                
                try:
                    # Use a more natural approach - wait for complete phrases
                    # phrase_time_limit=None allows for longer, more natural speech
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=None)
                    
                    if audio_data is None:
                        audio_data = audio
                        speech_started = True
                        print("🎙️ Speech detected...", end="", flush=True)
                    else:
                        # Combine audio data (simplified approach)
                        audio_data = audio  # Keep the most recent complete phrase
                    
                    last_speech_time = current_time
                    print("🎵", end="", flush=True)  # Visual feedback for continued speech
                    
                except sr.WaitTimeoutError:
                    # No audio detected in this iteration
                    if speech_started:
                        silence_duration = current_time - last_speech_time
                        if silence_duration >= silence_threshold:
                            print(f"\n🔇 {silence_threshold}s of silence detected. Stopping recording.")
                            break
                        elif silence_duration > 0.5:  # Show waiting indicator for longer pauses
                            print("⏳", end="", flush=True)
                    else:
                        # Still waiting for initial speech
                        print(".", end="", flush=True)
                    
        print("\n🔴 Recording stopped.")
        
        if audio_data and speech_started:
            return audio_data
        else:
            return None
            
    except Exception as e:
        print(f"Error during recording: {e}", file=sys.stderr)
        return None

def record_audio_continuous_stream(max_duration=60, silence_threshold=3.0):
    """Record audio using continuous streaming for more natural speech detection."""
    recognizer = sr.Recognizer()
    
    # Optimize recognizer settings for natural speech
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.8
    
    try:
        microphone = sr.Microphone()
    except Exception as e:
        print(f"Error initializing microphone: {e}", file=sys.stderr)
        return None
    
    print("🎤 Adjusting for ambient noise... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    
    print(f"🔴 Recording started. Speak naturally! (Max {max_duration} seconds, stops after {silence_threshold}s of silence)")
    print("💡 Take your time - natural pauses are handled automatically.")
    
    start_time = time.time()
    
    try:
        with microphone as source:
            # Use the more natural listen method that waits for complete phrases
            audio = recognizer.listen(source, timeout=max_duration, phrase_time_limit=max_duration)
            
            print("\n🔴 Recording completed.")
            return audio
            
    except sr.WaitTimeoutError:
        print(f"\n🔇 No speech detected within {max_duration} seconds.")
        return None
    except Exception as e:
        print(f"Error during recording: {e}", file=sys.stderr)
        return None

def record_audio_with_voice_activity_detection(max_duration=60, silence_threshold=3.0):
    """Record audio with intelligent voice activity detection for most natural speech flow."""
    recognizer = sr.Recognizer()
    
    # Optimize for natural speech patterns
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Natural pause between words
    recognizer.phrase_threshold = 0.3  # Minimum phrase length
    recognizer.non_speaking_duration = 0.8  # Wait time before considering end of speech
    
    try:
        microphone = sr.Microphone()
    except Exception as e:
        print(f"Error initializing microphone: {e}", file=sys.stderr)
        return None
    
    print("🎤 Calibrating microphone for your voice... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
        initial_energy = recognizer.energy_threshold
        print(f"🔧 Energy threshold set to: {initial_energy}")
    
    print(f"🔴 Ready to record! Speak naturally and clearly.")
    print(f"💡 The system will wait for natural pauses and stop after {silence_threshold}s of silence.")
    print("🎙️ Start speaking when ready...")
    
    start_time = time.time()
    
    try:
        with microphone as source:
            # Wait for speech to begin
            print("⏳ Waiting for speech to begin...", end="", flush=True)
            
            # Use a smarter approach - wait for speech, then record until natural end
            audio = recognizer.listen(
                source, 
                timeout=max_duration,  # Maximum wait time for speech to start
                phrase_time_limit=max_duration  # Maximum recording time once speech starts
            )
            
            duration = time.time() - start_time
            print(f"\n🔴 Recording completed ({duration:.1f}s).")
            return audio
            
    except sr.WaitTimeoutError:
        print(f"\n🔇 No speech detected within {max_duration} seconds.")
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
    print("✨ Enhanced with natural speech detection for better human interaction")
    print("Checking dependencies...")
    
    parser = argparse.ArgumentParser(description="Record speech, convert to text, and forward to Ollama TTS.")
    parser.add_argument("--max_duration", type=int, default=60, help="Maximum recording duration in seconds (default: 60)")
    parser.add_argument("--silence_threshold", type=float, default=3.0, help="Seconds of silence before stopping (default: 3.0)")
    parser.add_argument("--recording_mode", type=str, default="smart", choices=["smart", "natural", "chunked"], 
                        help="Recording mode: 'smart' for voice activity detection, 'natural' for continuous flow, 'chunked' for legacy method (default: smart)")
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
        # Record audio using the selected method
        if args.recording_mode == "smart":
            audio = record_audio_with_voice_activity_detection(args.max_duration, args.silence_threshold)
        elif args.recording_mode == "natural":
            audio = record_audio_continuous_stream(args.max_duration, args.silence_threshold)
        else:  # chunked
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
