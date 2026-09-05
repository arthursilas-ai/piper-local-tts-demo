#!/usr/bin/env python3
"""
list_voices.py — Browse and download Piper voices

Lists available Piper voices, optionally filtered by language, and
generates the correct download command for any voice you pick.

Usage:
    python list_voices.py                   # list all English voices
    python list_voices.py --lang en_GB      # British English only
    python list_voices.py --lang de         # German voices
    python list_voices.py --lang all        # every language
    python list_voices.py --download en_GB-alan-medium   # print download command

All voices: https://rhasspy.github.io/piper-samples/
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

VOICES_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json"
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Curated starter picks — good quality, common use cases
RECOMMENDED = {
    "en_GB-alan-medium": "British English, male, general purpose",
    "en_GB-alba-medium": "British English, female, clear",
    "en_US-lessac-medium": "American English, female, neutral",
    "en_US-ryan-medium": "American English, male, natural",
    "de_DE-thorsten-medium": "German, male, clear",
    "fr_FR-siwis-medium": "French, female, natural",
    "es_ES-carlfm-x_low": "Spanish, male, lightweight",
}


def fetch_voices() -> dict:
    try:
        with urllib.request.urlopen(VOICES_JSON_URL, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        sys.exit(f"Could not fetch voices list: {e}\nCheck your internet connection.")


def download_command(voice_key: str, voice_dir: str = "voices") -> str:
    """Generate the curl commands to download a voice."""
    # voice_key format: lang_REGION-name-quality e.g. en_GB-alan-medium
    parts = voice_key.split("-")
    if len(parts) < 3:
        return f"# Could not parse voice key: {voice_key}"

    lang_region = parts[0]  # e.g. en_GB
    lang = lang_region.split("_")[0]  # e.g. en
    region = lang_region.split("_")[1].lower() if "_" in lang_region else lang_region  # e.g. gb
    name = parts[1]  # e.g. alan
    quality = parts[2]  # e.g. medium

    onnx_name = f"{voice_key}.onnx"
    json_name = f"{voice_key}.onnx.json"
    hf_path = f"{lang}/{lang_region}/{name}/{quality}"

    lines = [
        f"mkdir -p {voice_dir}",
        f'curl -L -o {voice_dir}/{onnx_name} "{HF_BASE}/{hf_path}/{onnx_name}"',
        f'curl -L -o {voice_dir}/{json_name} "{HF_BASE}/{hf_path}/{json_name}"',
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Browse and download Piper TTS voices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--lang", default="en",
        help="Language filter: 'en', 'en_GB', 'de', 'fr', or 'all' (default: en)"
    )
    ap.add_argument(
        "--quality",
        choices=["x_low", "low", "medium", "high"],
        help="Filter by quality tier",
    )
    ap.add_argument(
        "--download",
        metavar="VOICE_KEY",
        help="Print the download command for a specific voice (e.g. en_GB-alan-medium)",
    )
    ap.add_argument(
        "--voice-dir", default="voices",
        help="Target directory for --download (default: voices)",
    )
    args = ap.parse_args()

    if args.download:
        print(f"# Download {args.download}:")
        print(download_command(args.download, args.voice_dir))
        return

    print("Fetching voice list from HuggingFace…")
    voices = fetch_voices()

    lang_filter = None if args.lang == "all" else args.lang.lower()

    rows = []
    for key, meta in voices.items():
        lang = (meta.get("language", {}).get("code") or "").lower()
        quality = meta.get("quality", "")
        name = meta.get("name", key)

        if lang_filter:
            if not lang.startswith(lang_filter):
                continue
        if args.quality and quality != args.quality:
            continue

        size_mb = round(meta.get("files", {}).get(f"{key}.onnx", {}).get("size_bytes", 0) / 1_000_000, 0)
        size_str = f"~{int(size_mb)}MB" if size_mb else "?"
        rows.append((key, quality, size_str, name))

    if not rows:
        print(f"No voices found for filter: lang={args.lang!r}, quality={args.quality!r}")
        return

    rows.sort(key=lambda r: (r[0], r[1]))

    print(f"\n{'Voice key':<40} {'Quality':<10} {'Size':<8} Notes")
    print("-" * 80)
    for key, quality, size, name in rows:
        rec = " ← recommended" if key in RECOMMENDED else ""
        print(f"{key:<40} {quality:<10} {size:<8}{rec}")

    print(f"\n{len(rows)} voice(s) found.\n")
    print("Download a voice:")
    print("  python list_voices.py --download <voice-key>")
    print("  # then run the printed curl commands\n")
    print("Full samples at: https://rhasspy.github.io/piper-samples/")

    # Show recommended picks for the language
    recs = {k: v for k, v in RECOMMENDED.items() if lang_filter and k.startswith(lang_filter)}
    if recs:
        print("\nRecommended for this language:")
        for k, v in recs.items():
            print(f"  {k:<40} {v}")


if __name__ == "__main__":
    main()
