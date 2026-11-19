#!/usr/bin/env bash
# Bulut ortamı kurulumu: Python bağımlılıkları, Chromium, ffmpeg, Dart SDK.
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -q -r requirements.txt
python -m playwright install --with-deps chromium
sudo_cmd=""; command -v sudo >/dev/null && [ "$(id -u)" != 0 ] && sudo_cmd="sudo"
$sudo_cmd apt-get update -qq
$sudo_cmd apt-get install -y -qq ffmpeg apt-transport-https wget gnupg
if ! command -v dart >/dev/null; then
  wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | $sudo_cmd gpg --dearmor -o /usr/share/keyrings/dart.gpg
  echo 'deb [signed-by=/usr/share/keyrings/dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | $sudo_cmd tee /etc/apt/sources.list.d/dart_stable.list >/dev/null
  $sudo_cmd apt-get update -qq && $sudo_cmd apt-get install -y -qq dart
  export PATH="$PATH:/usr/lib/dart/bin"
fi
dart --version && ffmpeg -version | head -1
