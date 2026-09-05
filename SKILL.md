---
name: piper-local-tts-demo
description: Local, offline text-to-speech using Piper. Use when something needs to speak text aloud without a cloud API — home automation announcements, reading a script or file aloud, a local HTTP endpoint another service can call, or when privacy/cost rules out a cloud TTS provider entirely.
---

# Piper Local TTS Demo

Runs [Piper](https://github.com/rhasspy/piper) — a fast, offline TTS
engine — entirely on the local machine. No account, no per-word cost, no
text ever leaves the device.

## Run it

```bash
python speak.py "Dinner is ready."                    # speak once
python server.py                                     # local HTTP endpoint (port 5000)
python home_announcer.py --template washing           # smart-home style announcer
python batch.py announcements.txt --export wav_output/  # batch export to WAV
python list_voices.py --lang en_GB                     # browse available voices
```

`server.py` exposes `curl "http://localhost:5000/speak?text=..."`, so any
script, Home Assistant automation, or Node-RED flow can trigger speech with
one request.

## When to use it

- A smart-home or automation setup needs spoken announcements without a
  cloud dependency (Home Assistant, Node-RED, a Raspberry Pi).
- Reading a document, script, or queued set of messages aloud locally.
- Privacy or cost rules out routing text through a commercial TTS API.
- Wiring a voice layer onto a local LLM stack — see `sovereign-ai-harness`
  for how this fits alongside a local model.

## Install

```bash
pip install git+https://github.com/arthursilas-ai/piper-local-tts-demo.git
./download_voice.sh
piper-speak "The future belongs to those who own their tools."
```

Installs five commands: `piper-speak`, `piper-server`, `piper-announce`,
`piper-batch`, `piper-voices`.

Or as an agent skill: `npx skills add arthursilas-ai/piper-local-tts-demo`
