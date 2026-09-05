#!/usr/bin/env python3
"""
batch.py — Speak or export multiple lines of text in sequence

Reads from a text file (or stdin), speaks each non-empty line in order.
Useful for reading documents aloud, processing announcement queues, or
generating a folder of named WAV files.

Usage:
    python batch.py announcements.txt                  # speak each line
    python batch.py announcements.txt --export out/    # save as WAV files
    python batch.py announcements.txt --delay 1.5      # pause between lines
    cat announcements.txt | python batch.py            # from stdin
    python batch.py --demo                             # run a built-in demo

Export format:
    out/001_hello_from_your.wav
    out/002_dinner_is_ready.wav
    ...

Named export (prefix each line with "filename: text"):
    morning: Good morning. The time is eight o'clock.
    wash: The washing machine has finished.
    → out/morning.wav, out/wash.wav
"""

import argparse
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_VOICE = "voices/en_GB-alan-medium.onnx"

DEMO_LINES = [
    "This is piper-local-tts-demo, running on your own hardware.",
    "No internet connection required.",
    "No cloud account. No subscription. No one listening.",
    "Your voice. Your machine.",
]


def speak_wav(wav_path: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["afplay", wav_path], check=True)
    elif sys.platform == "linux":
        try:
            subprocess.run(["aplay", wav_path], check=True, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            subprocess.run(["paplay", wav_path], check=True)
    elif sys.platform == "win32":
        subprocess.run(
            ["powershell", "-c", f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync()"],
            check=True,
        )


def generate_wav_file(text: str, out_path: Path, voice: str) -> None:
    subprocess.run(
        ["piper", "--model", voice, "--output_file", str(out_path)],
        input=text,
        capture_output=True,
        text=True,
        check=True,
    )


def safe_filename(text: str, n: int) -> str:
    """Turn a line of text into a safe filename prefix."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]
    return f"{n:03d}_{slug}"


def parse_named(line: str) -> tuple[str | None, str]:
    """Parse 'name: text' lines. Returns (name, text) or (None, text)."""
    if ": " in line:
        name, _, text = line.partition(": ")
        name = name.strip()
        if re.match(r"^[a-z0-9_\-]+$", name):
            return name, text.strip()
    return None, line.strip()


def run_batch(
    lines: list[str],
    voice: str,
    export_dir: Path | None,
    delay: float,
    play: bool,
) -> None:
    named_mode = any(": " in ln and re.match(r"^[a-z0-9_\-]+: ", ln) for ln in lines)

    for i, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue

        name, text = parse_named(raw) if named_mode else (None, raw)

        if export_dir:
            stem = name if name else safe_filename(text, i)
            out_path = export_dir / f"{stem}.wav"
            try:
                generate_wav_file(text, out_path, voice)
                print(f"  [{i:03d}] saved → {out_path.name}")
                if play:
                    speak_wav(str(out_path))
                    if delay:
                        time.sleep(delay)
            except subprocess.CalledProcessError as e:
                print(f"  [{i:03d}] ERROR: {e.stderr}", file=sys.stderr)
        else:
            # Speak to a temp file, play, delete
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = Path(f.name)
            try:
                generate_wav_file(text, tmp, voice)
                label = f"[{i:03d}/{len(lines):03d}]"
                print(f"  {label} {text[:70]}")
                if play:
                    speak_wav(str(tmp))
                if delay:
                    time.sleep(delay)
            except subprocess.CalledProcessError as e:
                print(f"  [{i:03d}] ERROR: {e.stderr}", file=sys.stderr)
            finally:
                tmp.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Speak or export multiple lines of text using local Piper TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("file", nargs="?", help="Text file to process (default: stdin)")
    ap.add_argument("--voice", "-v", default=DEFAULT_VOICE, help="Piper voice model path")
    ap.add_argument("--export", "-e", metavar="DIR", help="Export as WAV files to this directory")
    ap.add_argument("--delay", "-d", type=float, default=0.3, help="Seconds to pause between lines (default: 0.3)")
    ap.add_argument("--no-play", action="store_true", help="Generate WAV files only, do not play")
    ap.add_argument("--demo", action="store_true", help="Run a built-in demo")
    args = ap.parse_args()

    # Check Piper installed
    try:
        subprocess.run(["piper", "--help"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit("Piper not found. Install with: pip install piper-tts")

    if not Path(args.voice).exists():
        sys.exit(f"Voice not found: {args.voice}\nRun ./download_voice.sh first.")

    if args.demo:
        lines = DEMO_LINES
    elif args.file:
        lines = Path(args.file).read_text().splitlines()
    elif not sys.stdin.isatty():
        lines = sys.stdin.read().splitlines()
    else:
        ap.print_help()
        sys.exit(1)

    export_dir = None
    if args.export:
        export_dir = Path(args.export)
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"Exporting WAV files to {export_dir}/")

    play = not args.no_play
    if not play and not export_dir:
        print("Note: --no-play with no --export means no output will be produced.")

    run_batch(lines, args.voice, export_dir, args.delay, play)
    print("Done.")


if __name__ == "__main__":
    main()
