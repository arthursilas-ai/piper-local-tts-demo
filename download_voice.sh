#!/bin/bash
# Download the default British English voice for Piper TTS
# Run this once after cloning the repo

set -e

VOICE_DIR="voices"
VOICE_NAME="en_GB-alan-medium"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium"

echo "Creating voices directory..."
mkdir -p "$VOICE_DIR"

echo "Downloading $VOICE_NAME model (~60MB)..."
curl -L -o "$VOICE_DIR/${VOICE_NAME}.onnx" \
  "$BASE_URL/${VOICE_NAME}.onnx"

echo "Downloading voice config..."
curl -L -o "$VOICE_DIR/${VOICE_NAME}.onnx.json" \
  "$BASE_URL/${VOICE_NAME}.onnx.json"

echo ""
echo "Done! Voice downloaded to $VOICE_DIR/"
echo "Test it with: python speak.py 'Hello from your own machine'"
