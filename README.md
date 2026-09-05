# piper-local-tts-demo

**Local text-to-speech. Your machine, your voice, no cloud required.**

Run [Piper](https://github.com/rhasspy/piper) — a fast, offline TTS engine — on your own hardware. Speak any text aloud without sending a single byte to the internet.

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

---

## Why this matters

Most text-to-speech today routes through cloud APIs — every word goes to Google, Amazon, or Microsoft. Piper flips this:

- **Runs entirely on your machine** — laptop, desktop, Raspberry Pi
- **Works offline** — no internet after setup
- **No ongoing costs** — nothing per word, per month, ever
- **Private by default** — your text stays on your hardware

This is the difference between renting a voice and owning one.

---

## Quick start

```bash
# 1. Install Piper
pip install piper-tts

# 2. Download a voice (~60MB, one time)
./download_voice.sh

# 3. Speak something
python speak.py "The future belongs to those who own their tools."
```

That is the whole thing. No account, no key, no internet after step 2.

---

## What is in this repo

| File | What it does |
|------|-------------|
| `speak.py` | Speak any text from the command line or stdin |
| `home_announcer.py` | Practical home announcement system with templates |
| `batch.py` | Speak or export a text file line by line |
| `server.py` | Local HTTP server — curl to speak, works with Home Assistant / Node-RED |
| `list_voices.py` | Browse and download Piper voices by language |
| `download_voice.sh` | Download the default British English voice |

---

## speak.py — basic usage

```bash
# Say something
python speak.py "Dinner is ready."

# Save to a WAV file instead of playing
python speak.py --output announcement.wav "Meeting in five minutes."

# Read from stdin (pipe-friendly)
echo "Task complete." | python speak.py

# Use a different voice
python speak.py --voice voices/en_US-lessac-medium.onnx "Hello from the US."
```

---

## server.py — HTTP endpoint for home automation

Run a local HTTP server so any script, smart home system, or browser tab can trigger speech:

```bash
python server.py              # starts on port 5000
python server.py --port 8080  # different port
```

Then from anywhere on the same machine (or your local network):

```bash
# Speak something
curl "http://localhost:5000/speak?text=Dinner+is+ready"

# POST with JSON
curl -X POST http://localhost:5000/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Motion detected in the kitchen."}'

# Built-in templates
curl http://localhost:5000/template/time     # "The time is 3:45 PM."
curl http://localhost:5000/template/washing  # "The washing machine has finished."
curl http://localhost:5000/template/morning  # "Good morning. Today is Saturday..."

# Download the WAV instead of playing (useful for remote clients)
curl "http://localhost:5000/speak?text=Hello&download=1" -o hello.wav

# Health check
curl http://localhost:5000/health
```

**Browser UI:** open `http://localhost:5000` for a simple web interface.

### Home Assistant integration

```yaml
# configuration.yaml
shell_command:
  announce: 'curl -s "http://localhost:5000/speak?text={{ message }}"'

# Then in an automation:
service: shell_command.announce
data:
  message: "Front door opened."
```

### Node-RED integration

Use the HTTP Request node: `POST http://localhost:5000/speak` with JSON body `{"text": "{{ msg.payload }}"}`.

---

## home_announcer.py — smart home announcer

A class-based announcer with templates, urgent repeat, and a real attention chime:

```bash
python home_announcer.py "Washing machine finished"
python home_announcer.py --urgent "Front door opened"   # says it twice
python home_announcer.py --chime "Package delivered"    # beep then speak
python home_announcer.py --time                         # "The time is 3:45 PM."
python home_announcer.py --template washing
python home_announcer.py --list-templates               # show all templates
```

**Available templates:** time, reminder, timer, door, washing, weather.

---

## batch.py — process a text file

Speak or export multiple lines in sequence:

```bash
# Speak every line in a file
python batch.py announcements.txt

# Export as numbered WAV files
python batch.py announcements.txt --export wav_output/

# Named exports: prefix each line with "name: "
echo "morning: Good morning, it is eight o clock." >> named.txt
echo "wash: The washing machine has finished."     >> named.txt
python batch.py named.txt --export wav_output/
# produces: wav_output/morning.wav, wav_output/wash.wav

# Pipe from stdin
cat script.txt | python batch.py

# Built-in demo
python batch.py --demo
```

---

## list_voices.py — browse available voices

Piper has voices in 30+ languages:

```bash
python list_voices.py                              # all English voices
python list_voices.py --lang en_GB                 # British English only
python list_voices.py --lang de                    # German
python list_voices.py --lang all                   # every language
python list_voices.py --download en_US-ryan-medium # print download command
```

**Recommended voices:**

| Voice key | Description |
|-----------|------------|
| `en_GB-alan-medium` | British English, male, general purpose |
| `en_GB-alba-medium` | British English, female, clear |
| `en_US-lessac-medium` | American English, female, neutral |
| `en_US-ryan-medium` | American English, male, natural |
| `de_DE-thorsten-medium` | German, male, clear |
| `fr_FR-siwis-medium` | French, female, natural |

Full list and audio samples: https://rhasspy.github.io/piper-samples/

---

## Hardware performance

| Device | Short phrase | Notes |
|--------|-------------|-------|
| MacBook Pro M1 | < 50ms | Near-instant |
| ThinkPad T480 (i5) | ~80ms | Fast enough |
| Raspberry Pi 4 (4GB) | ~200ms | Good for announcements |
| Raspberry Pi 3 | ~500ms | Noticeable delay, still works |

Disk: ~50–100MB per voice. RAM: ~200MB during inference.

---

## What this connects to

Piper is one piece of a stack that runs entirely on your own hardware:

- **Whisper** (speech-to-text) + **Piper** (text-to-speech) = local voice interface
- Add a local LLM (Llama, Mistral, Phi) = voice assistant with no cloud at all
- No subscriptions, no one listening, no vendor lock-in

---

## Learn more

- [Piper GitHub](https://github.com/rhasspy/piper)
- [Voice samples](https://rhasspy.github.io/piper-samples/)
- [Rhasspy project](https://rhasspy.readthedocs.io/)

---

*A [Solystopia](https://solystopia.tech) tool showcase — AI tools that run on hardware you own.*
