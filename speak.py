#!/usr/bin/env python3
"""
speak.py — Simple local text-to-speech using Piper

Usage:
    python speak.py "Your text here"
    python speak.py --voice voices/en_GB-alan-medium.onnx "Your text here"
    echo "Text from stdin" | python speak.py
"""

import argparse
import subprocess
import sys
import tempfile
import os
from pathlib import Path

# Default voice model (download with download_voice.sh)
DEFAULT_VOICE = "voices/en_GB-alan-medium.onnx"


def speak(text: str, voice_model: str = DEFAULT_VOICE, play: bool = True) -> Path:
    """
    Convert text to speech using Piper.
    
    Args:
        text: The text to speak
        voice_model: Path to the .onnx voice model file
        play: Whether to play the audio immediately
        
    Returns:
        Path to the generated .wav file
    """
    # Check if voice model exists
    if not Path(voice_model).exists():
        print(f"Voice model not found: {voice_model}")
        print("Run ./download_voice.sh first, or specify a different --voice")
        sys.exit(1)
    
    # Create output file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = Path(f.name)
    
    # Run Piper
    try:
        result = subprocess.run(
            ["piper", "--model", voice_model, "--output_file", str(output_path)],
            input=text,
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        print("Piper not found. Install it with: pip install piper-tts")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Piper error: {e.stderr}")
        sys.exit(1)
    
    # Play the audio if requested
    if play:
        play_audio(output_path)
    
    return output_path


def play_audio(path: Path) -> None:
    """Play a .wav file using the system's default player."""
    system = sys.platform
    
    try:
        if system == "darwin":  # macOS
            subprocess.run(["afplay", str(path)], check=True)
        elif system == "linux":
            # Try aplay first (ALSA), fall back to paplay (PulseAudio)
            try:
                subprocess.run(["aplay", str(path)], check=True, 
                             stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                subprocess.run(["paplay", str(path)], check=True)
        elif system == "win32":
            # Windows - use PowerShell
            subprocess.run(
                ["powershell", "-c", f"(New-Object Media.SoundPlayer '{path}').PlaySync()"],
                check=True
            )
        else:
            print(f"Don't know how to play audio on {system}")
            print(f"Audio saved to: {path}")
    except subprocess.CalledProcessError:
        print(f"Could not play audio. File saved to: {path}")
    except FileNotFoundError:
        print(f"No audio player found. File saved to: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Speak text aloud using local Piper TTS",
        epilog="Example: python speak.py 'Hello from your own machine'"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to speak (or pipe from stdin)"
    )
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"Path to Piper voice model (default: {DEFAULT_VOICE})"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save to file instead of playing"
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Don't play audio, just save to temp file"
    )
    
    args = parser.parse_args()
    
    # Get text from argument or stdin
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("No text provided. Usage: python speak.py 'Your text here'")
        sys.exit(1)
    
    if not text:
        print("Empty text provided")
        sys.exit(1)
    
    # Generate speech
    output_path = speak(
        text,
        voice_model=args.voice,
        play=not args.no_play and not args.output
    )
    
    # Copy to specified output if requested
    if args.output:
        import shutil
        shutil.copy(output_path, args.output)
        print(f"Saved to: {args.output}")
    elif args.no_play:
        print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
