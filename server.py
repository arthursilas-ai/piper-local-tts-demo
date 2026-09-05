#!/usr/bin/env python3
"""
server.py — Local HTTP server for Piper TTS

Runs a small HTTP server on localhost so any script, smart home system,
or browser tab can trigger speech with a single request. No cloud, no
account — audio plays on the machine running this server.

Usage:
    python server.py                   # start on port 5000
    python server.py --port 8080       # different port
    python server.py --no-play         # return WAV bytes instead of playing

Speak something:
    curl "http://localhost:5000/speak?text=Dinner+is+ready"
    curl -X POST http://localhost:5000/speak -d '{"text": "Hello"}' -H "Content-Type: application/json"
    curl "http://localhost:5000/speak?text=Hello&download=1" -o hello.wav

Home Assistant / Node-RED:
    POST http://localhost:5000/speak
    Body: {"text": "Motion detected in the kitchen"}

Templates (same as home_announcer.py):
    curl "http://localhost:5000/template/time"
    curl "http://localhost:5000/template/washing"

Health check:
    curl http://localhost:5000/health
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_VOICE = "voices/en_GB-alan-medium.onnx"
DEFAULT_PORT = 5000

TEMPLATES = {
    "time": lambda: f"The time is {datetime.now().strftime('%I:%M %p').lstrip('0')}.",
    "washing": lambda: "The washing machine has finished.",
    "timer": lambda: "Your timer is up.",
    "door": lambda: "The front door has been opened.",
    "morning": lambda: f"Good morning. Today is {datetime.now().strftime('%A, %d %B')}.",
}


def _check_setup(voice_model: str) -> None:
    try:
        subprocess.run(["piper", "--help"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit("Piper not found. Install with: pip install piper-tts")

    if not Path(voice_model).exists():
        sys.exit(
            f"Voice model not found: {voice_model}\n"
            "Run ./download_voice.sh to download the default voice."
        )


def generate_wav(text: str, voice_model: str) -> bytes:
    """Generate WAV bytes for `text` using Piper."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out = Path(f.name)

    try:
        subprocess.run(
            ["piper", "--model", voice_model, "--output_file", str(out)],
            input=text,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.read_bytes()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Piper error: {e.stderr}") from e
    finally:
        out.unlink(missing_ok=True)


def play_wav(wav_bytes: bytes) -> None:
    """Write bytes to a temp file and play through the system player."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        Path(f.name).write_bytes(wav_bytes)
        path = f.name

    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", path], check=True)
        elif sys.platform == "linux":
            try:
                subprocess.run(["aplay", path], check=True, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                subprocess.run(["paplay", path], check=True)
        elif sys.platform == "win32":
            subprocess.run(
                ["powershell", "-c", f"(New-Object Media.SoundPlayer '{path}').PlaySync()"],
                check=True,
            )
    finally:
        Path(path).unlink(missing_ok=True)


class TTSHandler(BaseHTTPRequestHandler):
    """HTTP request handler. Set .voice_model and .play_audio as class attrs."""

    voice_model: str = DEFAULT_VOICE
    play_audio: bool = True

    def log_message(self, fmt: str, *args) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {fmt % args}")

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self._send(code, "application/json", body)

    def _parse_text(self) -> str | None:
        """Extract text from query string or JSON body."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "text" in params:
            return params["text"][0].strip()

        # Try JSON body
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try:
                body = json.loads(self.rfile.read(length))
                return str(body.get("text", "")).strip()
            except (json.JSONDecodeError, ValueError):
                return None

        return None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/health":
            self._json(200, {
                "ok": True,
                "voice": self.voice_model,
                "play": self.play_audio,
                "ts": datetime.utcnow().isoformat() + "Z",
            })
            return

        if path.startswith("/template/"):
            name = path.split("/template/")[-1]
            if name not in TEMPLATES:
                self._json(404, {"error": f"Unknown template: {name}", "available": list(TEMPLATES)})
                return
            text = TEMPLATES[name]()
            self._speak(text, parsed.query)
            return

        if path == "/speak":
            text = self._parse_text()
            if not text:
                self._json(400, {"error": "Provide text via ?text= query param or JSON body"})
                return
            self._speak(text, parsed.query)
            return

        if path in ("", "/"):
            body = _index_html().encode()
            self._send(200, "text/html; charset=utf-8", body)
            return

        self._json(404, {"error": "Not found", "routes": ["/speak", "/template/<name>", "/health"]})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/speak":
            text = self._parse_text()
            if not text:
                self._json(400, {"error": "Provide text via ?text= query param or JSON body"})
                return
            self._speak(text, parsed.query)
            return

        self._json(404, {"error": "Not found"})

    def _speak(self, text: str, query_string: str) -> None:
        params = urllib.parse.parse_qs(query_string)
        want_download = "download" in params or "wav" in params

        try:
            t0 = time.perf_counter()
            wav = generate_wav(text, self.voice_model)
            ms = int((time.perf_counter() - t0) * 1000)
            print(f"  generated {len(wav)//1024}KB in {ms}ms — \"{text[:60]}\"")
        except RuntimeError as e:
            self._json(500, {"error": str(e)})
            return

        if want_download:
            # Return WAV bytes — useful for remote clients
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav)))
            self.send_header("Content-Disposition", 'attachment; filename="speech.wav"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(wav)
            return

        # Play locally and return JSON confirmation
        if self.play_audio:
            play_wav(wav)

        self._json(200, {
            "ok": True,
            "text": text,
            "bytes": len(wav),
            "voice": Path(self.voice_model).name,
        })


def _index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Piper TTS — local server</title>
<style>
  body { font-family: monospace; max-width: 640px; margin: 48px auto; padding: 0 24px; background: #0a0a0a; color: #fafafa; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  p, label { color: #a1a1aa; font-size: .9rem; }
  textarea { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #27272a;
             background: #141414; color: #fafafa; font-size: 1rem; resize: vertical; }
  button { margin-top: 8px; padding: 10px 24px; border-radius: 999px; border: none;
           background: #3ddc84; color: #06210f; font-weight: 700; cursor: pointer; }
  #status { margin-top: 12px; font-size: .85rem; color: #a1a1aa; min-height: 1.4em; }
  code { background: #1c1c1c; padding: 2px 6px; border-radius: 4px; }
</style>
</head>
<body>
<h1>piper-local-tts — local server</h1>
<p>Running on your machine. No cloud, no account.</p>
<label for="txt">Text to speak</label><br>
<textarea id="txt" rows="4" placeholder="Type anything here..."></textarea><br>
<button onclick="speak()">Speak</button>
<div id="status"></div>
<hr style="border-color:#27272a;margin:32px 0">
<p>API:<br>
<code>curl "http://localhost:5000/speak?text=Hello"</code><br>
<code>curl http://localhost:5000/template/time</code><br>
<code>curl http://localhost:5000/health</code>
</p>
<script>
async function speak() {
  const text = document.getElementById('txt').value.trim();
  if (!text) return;
  document.getElementById('status').textContent = 'Speaking…';
  try {
    const r = await fetch('/speak', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const d = await r.json();
    document.getElementById('status').textContent = d.ok
      ? `✓ spoken (${d.bytes} bytes)`
      : `Error: ${d.error}`;
  } catch(e) {
    document.getElementById('status').textContent = `Error: ${e.message}`;
  }
}
document.getElementById('txt').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) speak();
});
</script>
</body>
</html>"""


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Local HTTP server for Piper TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--port", "-p", type=int, default=DEFAULT_PORT)
    ap.add_argument("--voice", "-v", default=DEFAULT_VOICE)
    ap.add_argument(
        "--no-play",
        action="store_true",
        help="Do not play audio locally — only return WAV on ?download=1 requests",
    )
    args = ap.parse_args()

    _check_setup(args.voice)

    TTSHandler.voice_model = args.voice
    TTSHandler.play_audio = not args.no_play

    server = HTTPServer(("localhost", args.port), TTSHandler)
    play_note = "" if args.no_play else " (audio plays on this machine)"
    print(f"piper-tts server listening on http://localhost:{args.port}{play_note}")
    print(f"  Voice: {args.voice}")
    print(f"  Speak: curl \"http://localhost:{args.port}/speak?text=Hello+world\"")
    print(f"  Time:  curl http://localhost:{args.port}/template/time")
    print(f"  Health: curl http://localhost:{args.port}/health")
    print("  Stop:  Ctrl+C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
