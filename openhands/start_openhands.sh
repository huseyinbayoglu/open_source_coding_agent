#!/usr/bin/env bash
# OpenHands'i baslatir -> GUI: http://localhost:3000
#
# Colab'daki Qwen3-Coder endpoint'i UI'dan baglanir (asagidaki README'ye bak).
# OpenHands tum toollari (bash, dosya olustur/sil, kod yaz, python, browser) hazir getirir;
# sen sadece rol/skill dosyalarini (.openhands/microagents/) projene koyarsin.
#
# NOT: OpenHands surum etiketleri hizli degisir. Calismazsa guncel komutu
#      https://docs.openhands.dev adresindeki "Setup" sayfasindan al, sadece imaj/tag'i guncelle.
set -euo pipefail

OH_VERSION="${OH_VERSION:-1.8}"                       # openhands app imaj tag'i
AGENT_SERVER_TAG="${AGENT_SERVER_TAG:-1.26.0-python}" # sandbox agent-server tag'i

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker bulunamadi. Once Docker Desktop kur ve calistir." >&2
  exit 1
fi

docker run -it --rm --pull=always \
  -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server \
  -e AGENT_SERVER_IMAGE_TAG="${AGENT_SERVER_TAG}" \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.openhands:/.openhands \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name openhands-app \
  "docker.openhands.dev/openhands/openhands:${OH_VERSION}"
