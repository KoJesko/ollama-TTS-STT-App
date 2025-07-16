#!/usr/bin/env python3
"""
Ollama STT Web Portal
A beautiful web interface for the Ollama Speech-to-Text application
"""

import os
import sys
import json
import threading
import subprocess
import time
from datetime import datetime
from pathlib import Path

def check_and_install_dependencies():
    """Check and install required dependencies on first run"""
    print("🔍 Checking dependencies...")
    
    # List of required packages with their import names
    required_packages = [
        ('Flask==3.0.0', 'flask'),
        ('SpeechRecognition==3.10.0', 'speech_recognition'),
        ('pyaudio==0.2.11', 'pyaudio'),
        ('pydub==0.25.1', 'pydub'),
        ('Werkzeug==3.0.1', 'werkzeug')
    ]
    
    missing_packages = []
    
    # Check each package
    for package_spec, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {import_name} is already installed")
        except ImportError:
            missing_packages.append(package_spec)
            print(f"❌ {import_name} is missing")
    
    # Install missing packages
    if missing_packages:
        print(f"📦 Installing {len(missing_packages)} missing packages...")
        try:
            # Upgrade pip first
            print("🔄 Upgrading pip...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         capture_output=True, text=True)
            
            # Install packages using pip
            for package in missing_packages:
                print(f"Installing {package}...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Successfully installed {package}")
                else:
                    print(f"❌ Failed to install {package}: {result.stderr}")
                    # Try installing without version constraint if specific version fails
                    package_name = package.split('==')[0]
                    print(f"🔄 Trying to install latest version of {package_name}...")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package_name
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ Successfully installed {package_name} (latest version)")
                    else:
                        print(f"❌ Failed to install {package_name}: {result.stderr}")
                        return False
            
            print("🎉 All dependencies installed successfully!")
            return True
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    else:
        print("✅ All dependencies are already installed!")
        return True

# Check and install dependencies before importing Flask modules
if not check_and_install_dependencies():
    print("❌ Failed to install dependencies. Please install them manually using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Now import Flask and other modules after ensuring dependencies are installed
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    import speech_recognition as sr
    import tempfile
    import base64
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please try installing dependencies manually using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

app = Flask(__name__)

# Configuration
PORT = 55667
HOST = '0.0.0.0'  # Bind to all interfaces for Docker compatibility
UPLOAD_FOLDER = 'uploads'
TRANSCRIPTION_FOLDER = 'transcriptions'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPTION_FOLDER, exist_ok=True)

# Global variables
recording_status = {"active": False, "text": ""}
transcription_history = []

class STTProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"Warning: Could not initialize microphone: {e}")
    
    def transcribe_audio_file(self, audio_file_path, engine="google"):
        """Transcribe an uploaded audio file"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            if engine == "google":
                text = self.recognizer.recognize_google(audio)
            elif engine == "whisper":
                text = self.recognizer.recognize_whisper(audio)
            else:
                text = self.recognizer.recognize_google(audio)
            
            return {"success": True, "text": text.strip()}
        except sr.UnknownValueError:
            return {"success": False, "error": "Could not understand the audio"}
        except sr.RequestError as e:
            return {"success": False, "error": f"Error with {engine} service: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    def record_and_transcribe(self, duration=10, engine="google"):
        """Record from microphone and transcribe"""
        if not self.microphone:
            return {"success": False, "error": "Microphone not available"}
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            if engine == "google":
                text = self.recognizer.recognize_google(audio)
            elif engine == "whisper":
                text = self.recognizer.recognize_whisper(audio)
            else:
                text = self.recognizer.recognize_google(audio)
            
            return {"success": True, "text": text.strip()}
        except sr.WaitTimeoutError:
            return {"success": False, "error": "No speech detected within timeout"}
        except sr.UnknownValueError:
            return {"success": False, "error": "Could not understand the audio"}
        except sr.RequestError as e:
            return {"success": False, "error": f"Error with {engine} service: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

stt_processor = STTProcessor()

@app.route('/')
def index():
    """Main portal page"""
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Handle transcription requests"""
    try:
        data = request.get_json()
        method = data.get('method', 'microphone')
        engine = data.get('engine', 'google')
        duration = int(data.get('duration', 10))
        
        if method == 'microphone':
            result = stt_processor.record_and_transcribe(duration=duration, engine=engine)
        else:
            return jsonify({"success": False, "error": "Invalid method"})
        
        if result["success"]:
            # Save to history
            transcription_entry = {
                "timestamp": datetime.now().isoformat(),
                "text": result["text"],
                "engine": engine,
                "method": method
            }
            transcription_history.append(transcription_entry)
            
            # Save to file
            save_transcription(result["text"])
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Handle audio file uploads"""
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"})
        
        file = request.files['audio']
        engine = request.form.get('engine', 'google')
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"})
        
        # Save uploaded file
        from werkzeug.utils import secure_filename
        filename = f"upload_{int(time.time())}_{secure_filename(file.filename)}"
        filepath = os.path.normpath(os.path.join(UPLOAD_FOLDER, filename))
        if not filepath.startswith(os.path.abspath(UPLOAD_FOLDER)):
            return jsonify({"success": False, "error": "Invalid file path"})
        file.save(filepath)
        
        # Transcribe
        result = stt_processor.transcribe_audio_file(filepath, engine=engine)
        
        if result["success"]:
            # Save to history
            transcription_entry = {
                "timestamp": datetime.now().isoformat(),
                "text": result["text"],
                "engine": engine,
                "method": "upload",
                "filename": filename
            }
            transcription_history.append(transcription_entry)
            
            # Save to file
            save_transcription(result["text"])
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history')
def get_history():
    """Get transcription history"""
    return jsonify({"history": transcription_history})

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear transcription history"""
    global transcription_history
    transcription_history = []
    return jsonify({"success": True})

@app.route('/api/forward-to-ollama', methods=['POST'])
def forward_to_ollama():
    """Forward text to Ollama for processing"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        model = data.get('model', 'llama3.1:latest')
        
        if not text:
            return jsonify({"success": False, "error": "No text provided"})
        
        # Try to run ollama command
        try:
            cmd = ['ollama', 'run', model, text]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return jsonify({"success": True, "response": result.stdout})
            else:
                return jsonify({"success": False, "error": result.stderr})
        except subprocess.TimeoutExpired:
            return jsonify({"success": False, "error": "Ollama request timed out"})
        except FileNotFoundError:
            return jsonify({"success": False, "error": "Ollama not found. Please ensure Ollama is installed and running."})
        except Exception as e:
            return jsonify({"success": False, "error": f"Error running Ollama: {str(e)}"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/system-info')
def system_info():
    """Get system information"""
    try:
        info = {
            "python_version": sys.version,
            "microphone_available": stt_processor.microphone is not None,
            "ollama_available": check_ollama_available(),
            "supported_engines": ["google", "whisper"],
            "transcription_count": len(transcription_history)
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)})

def check_ollama_available():
    """Check if Ollama is available"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def save_transcription(text):
    """Save transcription to file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{timestamp}.txt"
        filepath = os.path.join(TRANSCRIPTION_FOLDER, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Text: {text}\n")
    except Exception as e:
        print(f"Error saving transcription: {e}")

if __name__ == '__main__':
    print("🚀 Starting Ollama STT Web Portal...")
    print("📦 Automatic dependency installation enabled")
    print(f"📡 Server will run on http://{HOST}:{PORT}")
    print(f"🎙️  Microphone available: {stt_processor.microphone is not None}")
    print(f"🤖 Ollama available: {check_ollama_available()}")
    print("💡 Dependencies will be automatically installed if missing")
    print("=" * 50)
    
    app.run(host=HOST, port=PORT, debug=True)
