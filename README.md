# Piper Local TTS Demo

**Your voice, your machine, no cloud required.**

This demo shows how to run [Piper](https://github.com/rhasspy/piper) — a fast, local, offline text-to-speech engine — on your own hardware. Speak any text aloud without sending a single byte to the internet.

## Why this matters

Most text-to-speech today runs through cloud APIs: you send your text to Google, Amazon, or Microsoft, they process it, you get audio back. Every word you speak goes through their servers.

Piper flips this:
- **Runs entirely on your machine** — laptop, desktop, even Raspberry Pi
- **Works offline** — no internet connection needed after setup
- **No ongoing costs** — pay nothing per word, per month, ever
- **Private by default** — your text stays on your hardware

This is the difference between renting a voice and owning one.

## What you can build with this

- **Home announcements** — "Dinner's ready" from your smart home, without Alexa listening
- **Accessibility tools** — screen readers, document readers, notification speakers
- **Workshop alerts** — machine status, timer completions, safety warnings
- **Learning aids** — pronunciation practice, language learning, reading assistance
- **Kiosk/signage** — audio guidance without cloud dependencies

## The practical numbers

| Metric | Value |
|--------|-------|
| Setup time | ~10 minutes |
| Disk space | ~50-100MB per voice |
| RAM needed | ~200MB during inference |
| Hardware minimum | Raspberry Pi 4 / any laptop from 2015+ |
| Ongoing cost | £0 |
| Internet required | Only for initial download |
| Latency | <100ms for short phrases (CPU) |

## Quick start

### 1. Install Piper

```bash
# Using pip (easiest)
pip install piper-tts

# Or download the standalone binary from:
# https://github.com/rhasspy/piper/releases
```

### 2. Download a voice

Piper voices are small (~50-100MB). Pick one from [the voice list](https://rhasspy.github.io/piper-samples/).

```bash
# Example: download a British English voice
mkdir -p voices
cd voices

# Download model and config
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json
```

### 3. Speak something

```bash
# Command line
echo "Hello from your own machine" | piper \
  --model voices/en_GB-alan-medium.onnx \
  --output_file hello.wav

# Play it
aplay hello.wav      # Linux
afplay hello.wav     # macOS
```

Or use the Python script in this repo:

```bash
python speak.py "The future belongs to those who own their tools."
```

## Files in this demo

| File | Purpose |
|------|--------|
| `speak.py` | Simple script to speak any text |
| `home_announcer.py` | Practical example: home automation announcements |
| `download_voice.sh` | Helper script to download the default voice |

## Home announcer example

The `home_announcer.py` script shows a practical use case: a simple announcement system that could run on a Raspberry Pi in your home.

```bash
# Install dependencies
pip install piper-tts

# Announce something
python home_announcer.py "Washing machine finished"
python home_announcer.py "Dinner in ten minutes"
python home_announcer.py "Front door opened" --urgent
```

## Voices available

Piper has voices in 30+ languages. Some highlights:

- **English (UK)**: Alan, Alba, Cori (medium quality, ~60MB each)
- **English (US)**: Amy, Joe, Kusal, Lessac, Ryan (various qualities)
- **German**: Thorsten, Eva
- **French**: Siwis, Upmc
- **Spanish**: Carlfm, Davefx
- **And many more**: Welsh, Icelandic, Vietnamese, Swahili...

Full list: https://rhasspy.github.io/piper-samples/

## Hardware tested

| Device | Performance |
|--------|------------|
| MacBook Pro M1 | <50ms for short phrases |
| ThinkPad T480 (i5) | ~80ms for short phrases |
| Raspberry Pi 4 (4GB) | ~200ms for short phrases |
| Raspberry Pi 3 | ~500ms (usable, not instant) |

## Limitations

- **Voice quality**: Good, not indistinguishable from human. Fine for announcements and utility; you wouldn't use it for audiobooks.
- **No SSML**: Limited control over prosody/emphasis compared to cloud services.
- **English-centric**: Best voices are English; other languages vary in quality.

## What this connects to

This is one piece of a larger picture:

- **Whisper** (speech-to-text) + **Piper** (text-to-speech) = local voice interface
- Add a local LLM (Llama, Mistral) = voice assistant that runs entirely on your hardware
- No cloud, no subscriptions, no one listening

## Learn more

- [Piper GitHub](https://github.com/rhasspy/piper)
- [Voice samples](https://rhasspy.github.io/piper-samples/)
- [Rhasspy voice assistant project](https://rhasspy.readthedocs.io/)

---

*A [Solystopia](https://solystopia.org) tool showcase — demonstrating AI tools that run on hardware you own.*
