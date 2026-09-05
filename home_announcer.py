#!/usr/bin/env python3
"""
home_announcer.py — Home announcement system using local Piper TTS

A practical example of local text-to-speech for home automation.
Runs entirely on your own hardware — no cloud, no subscriptions.

Usage:
    python home_announcer.py "Dinner is ready"
    python home_announcer.py --urgent "Front door opened"
    python home_announcer.py --chime "Package delivered"

Integration ideas:
    - Cron job for scheduled announcements
    - MQTT subscription for smart home events
    - File watcher for specific triggers
    - HTTP endpoint for remote announcements
"""

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Configuration
DEFAULT_VOICE = "voices/en_GB-alan-medium.onnx"

# Announcement templates
TEMPLATES = {
    "time": "The time is {time}.",
    "reminder": "Reminder: {message}",
    "timer": "Timer complete. {message}",
    "door": "The {location} door has been opened.",
    "washing": "The washing machine has finished.",
    "weather": "Current weather: {conditions}, {temp} degrees.",
}


class HomeAnnouncer:
    """Simple home announcement system using local TTS."""
    
    def __init__(self, voice_model: str = DEFAULT_VOICE):
        self.voice_model = voice_model
        self._check_setup()
    
    def _check_setup(self):
        """Verify Piper is installed and voice model exists."""
        # Check Piper
        try:
            subprocess.run(
                ["piper", "--help"],
                capture_output=True,
                check=True
            )
        except FileNotFoundError:
            print("ERROR: Piper not installed.")
            print("Install with: pip install piper-tts")
            sys.exit(1)
        
        # Check voice model
        if not Path(self.voice_model).exists():
            print(f"ERROR: Voice model not found: {self.voice_model}")
            print("Run ./download_voice.sh or download a voice from:")
            print("https://rhasspy.github.io/piper-samples/")
            sys.exit(1)
    
    def _chime(self) -> None:
        """Play a brief attention beep using the system's built-in sounds."""
        if sys.platform == "darwin":
            # macOS: use afplay with a built-in system sound
            for sound in ("/System/Library/Sounds/Ping.aiff",
                          "/System/Library/Sounds/Tink.aiff"):
                if Path(sound).exists():
                    subprocess.run(["afplay", sound], check=False)
                    return
            # Fallback: terminal bell
            print("\a", end="", flush=True)
        elif sys.platform == "linux":
            # Try paplay with a freedesktop sound, fall back to terminal bell
            try:
                for sound in ("/usr/share/sounds/freedesktop/stereo/bell.oga",
                              "/usr/share/sounds/ubuntu/stereo/bell.ogg"):
                    if Path(sound).exists():
                        subprocess.run(["paplay", sound], check=False,
                                       stderr=subprocess.DEVNULL)
                        return
            except FileNotFoundError:
                pass
            print("\a", end="", flush=True)
        else:
            print("\a", end="", flush=True)

    def speak(self, text: str, urgent: bool = False, chime: bool = False):
        """
        Announce text through speakers.

        Args:
            text: The message to announce
            urgent: If True, repeat the message twice
            chime: If True, play an attention sound before speaking
        """
        if chime:
            self._chime()
        
        # Generate speech
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        subprocess.run(
            ["piper", "--model", self.voice_model, "--output_file", output_path],
            input=text,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Play announcement
        self._play(output_path)
        
        if urgent:
            time.sleep(0.5)
            self._play(output_path)
        
        # Cleanup
        Path(output_path).unlink(missing_ok=True)
    
    def _play(self, path: str):
        """Play audio file using system player."""
        if sys.platform == "darwin":
            subprocess.run(["afplay", path], check=True)
        elif sys.platform == "linux":
            try:
                subprocess.run(["aplay", path], check=True,
                             stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                subprocess.run(["paplay", path], check=True)
        elif sys.platform == "win32":
            subprocess.run(
                ["powershell", "-c", 
                 f"(New-Object Media.SoundPlayer '{path}').PlaySync()"],
                check=True
            )
    
    def announce_time(self):
        """Announce the current time."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        self.speak(f"The time is {time_str}.")
    
    def announce_from_template(self, template_name: str, **kwargs):
        """Use a predefined announcement template."""
        if template_name not in TEMPLATES:
            print(f"Unknown template: {template_name}")
            print(f"Available: {', '.join(TEMPLATES.keys())}")
            return
        
        text = TEMPLATES[template_name].format(**kwargs)
        self.speak(text)


def main():
    parser = argparse.ArgumentParser(
        description="Home announcement system using local Piper TTS",
        epilog="Example: python home_announcer.py 'Dinner is ready'"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to announce"
    )
    parser.add_argument(
        "--urgent", "-u",
        action="store_true",
        help="Repeat the message (for important announcements)"
    )
    parser.add_argument(
        "--chime", "-c",
        action="store_true",
        help="Play attention chime before announcement"
    )
    parser.add_argument(
        "--time", "-t",
        action="store_true",
        help="Announce the current time"
    )
    parser.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        help="Use a predefined template"
    )
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"Voice model path (default: {DEFAULT_VOICE})"
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="Show available announcement templates"
    )
    
    args = parser.parse_args()
    
    if args.list_templates:
        print("Available templates:")
        for name, template in TEMPLATES.items():
            print(f"  {name}: {template}")
        return
    
    announcer = HomeAnnouncer(voice_model=args.voice)
    
    if args.time:
        announcer.announce_time()
    elif args.template:
        # For templates, the message becomes a parameter
        kwargs = {"message": args.message} if args.message else {}
        announcer.announce_from_template(args.template, **kwargs)
    elif args.message:
        announcer.speak(args.message, urgent=args.urgent, chime=args.chime)
    else:
        print("No message provided.")
        print("Usage: python home_announcer.py 'Your message'")
        print("   or: python home_announcer.py --time")
        sys.exit(1)


if __name__ == "__main__":
    main()
