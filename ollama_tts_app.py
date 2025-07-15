import argparse
import sys
import subprocess
import importlib.util
from datetime import datetime
import os
import asyncio

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
        'ollama': 'ollama',
        'edge_tts': 'edge-tts',
        'pygame': 'pygame'
    }
    
    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"Package '{module_name}' not found. Installing...")
            install_package(package_name)
    
    # Now import the packages after ensuring they're installed
    global ollama, edge_tts, pygame
    try:
        import ollama
        import edge_tts
        import pygame
    except ImportError as e:
        print(f"Failed to import required packages: {e}", file=sys.stderr)
        print("Please try running the script again or manually install the packages.", file=sys.stderr)
        sys.exit(1)

# Check and install dependencies first
check_and_install_dependencies()
def query_ollama(client, model, prompt, verbose):
    """
    Queries the Ollama model, streams the response, and returns the full text
    and performance statistics.
    """
    print(f"User: {prompt}")
    print(f"\nAssistant (using {model}):")

    full_response = ""
    try:
        response_stream = client.chat(
            model=model, 
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
    except ollama.ResponseError as e:
        print(f"\nError: {e.error}", file=sys.stderr)
        print("Is the model '{model}' pulled and available in Ollama?", file=sys.stderr)
        sys.exit(1)

    final_stats = {}
    for chunk in response_stream:
        if 'message' in chunk and 'content' in chunk['message']:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            full_response += content
        if chunk.get('done'):
            final_stats = chunk
    
    print("\n")

    if verbose and final_stats:
        eval_count = final_stats.get('eval_count', 0)
        eval_duration = final_stats.get('eval_duration', 0)
        if eval_count > 0 and eval_duration > 0:
            tokens_per_sec = eval_count / (eval_duration / 1e9)
            print("-" * 20)
            print("Performance Metrics:")
            print(f"  - Tokens generated: {eval_count}")
            print(f"  - Generation time: {eval_duration / 1e9:.2f} seconds")
            print(f"  - Tokens per second: {tokens_per_sec:.2f}")
            print("-" * 20)
            print("\n")

    return full_response

def synthesize_and_process_audio(text, speaker_voice, seed, output_path=None, compile_tts=False):
    """
    Initializes TTS engine, synthesizes audio from text, and either plays it
    or saves it to a file.
    """
    if not text.strip():
        print("Ollama returned an empty response. Nothing to synthesize.", file=sys.stderr)
        return

    print("Initializing TTS engine...")
    
    # Available high-quality voices (you can change these)
    available_voices = {
        "female_us": "en-US-AriaNeural",
        "male_us": "en-US-GuyNeural", 
        "female_uk": "en-GB-SoniaNeural",
        "male_uk": "en-GB-RyanNeural",
        "female_au": "en-AU-NatashaNeural",
        "male_au": "en-AU-WilliamNeural"
    }
    
    # Use provided voice or default to female US
    if speaker_voice:
        if speaker_voice in available_voices.values():
            voice = speaker_voice
        elif speaker_voice in available_voices:
            voice = available_voices[speaker_voice]
        else:
            print(f"Warning: Voice '{speaker_voice}' not found. Using default.")
            print("Available voices:")
            for key, value in available_voices.items():
                print(f"  {key}: {value}")
            voice = available_voices["female_us"]
    else:
        voice = available_voices["female_us"]
    
    print(f"Using voice: {voice}")
    print("Synthesizing audio...")
    print(f"Using seed {seed} for reproducible output.")
    
    try:
        # Create TTSHistory directory if it doesn't exist
        documents_path = os.path.expanduser("~/Documents")
        tts_history_path = os.path.join(documents_path, "SchmidtSims", "TTSHistory")
        os.makedirs(tts_history_path, exist_ok=True)
        
        # Generate filename with timestamp if no output_path provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(tts_history_path, f"tts_output_{timestamp}.mp3")
        elif not os.path.isabs(output_path):
            # If relative path provided, put it in TTSHistory directory
            output_path = os.path.join(tts_history_path, output_path)
        
        # Ensure output path has .mp3 extension
        if not output_path.endswith('.mp3'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp3'
        
        print(f"Saving audio to {output_path}...")
        
        # Run the async TTS function
        asyncio.run(generate_speech(text, voice, output_path))
        
        print("Audio saved successfully.")
        
        # Play audio
        print("Playing audio...")
        play_audio(output_path)
        print("Playback finished.")
                
    except Exception as e:
        print(f"Error during audio synthesis: {e}", file=sys.stderr)
        sys.exit(1)

async def generate_speech(text, voice, output_path):
    """Generate speech using edge-tts and save to file."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def play_audio(file_path):
    """Play audio file using pygame."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        pygame.mixer.quit()
    except Exception as e:
        print(f"Error playing audio: {e}", file=sys.stderr)
        print("Audio file saved successfully, but playback failed.")

def main():
    print("🎙️  Ollama TTS App - Starting up...")
    print("Checking dependencies...")
    
    parser = argparse.ArgumentParser(description="Query Ollama and synthesize the response with realistic TTS.")
    parser.add_argument("prompt", type=str, help="The prompt to send to the Ollama model.")
    parser.add_argument("--model", type=str, default="llama3.1:latest", help="The Ollama model to use.")
    parser.add_argument("--seed", type=int, default=42, help="A seed for reproducible output.")
    parser.add_argument("--output_path", type=str, help="Optional. Path to save the generated audio as a .mp3 file.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output to see performance metrics like tokens/sec.")
    parser.add_argument("--voice", type=str, help="Optional. Voice to use (e.g., en-US-AriaNeural, en-US-GuyNeural).")
    
    args = parser.parse_args()

    try:
        client = ollama.Client()
        client.show(args.model) # Check if model exists
    except Exception:
        print(f"Error: Could not connect to Ollama or find model '{args.model}'.", file=sys.stderr)
        print("Please ensure Ollama is running and the model is pulled.", file=sys.stderr)
        sys.exit(1)

    # 1. Get response from Ollama
    ollama_response = query_ollama(client, args.model, args.prompt, args.verbose)

    # 2. Synthesize and process audio with TTS
    synthesize_and_process_audio(ollama_response, args.voice, args.seed, args.output_path, False)

if __name__ == "__main__":
    main()