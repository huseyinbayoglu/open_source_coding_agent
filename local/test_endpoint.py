#!/usr/bin/env python3
"""
Colab endpoint'ini lokalden test eder:
  1) Endpoint ayakta mi / model adi ne?
  2) Basit sohbet calisiyor mu?
  3) TOOL-CALLING calisiyor mu?  <-- coding agent icin en kritik kisim

Kullanim:
    python test_endpoint.py https://xxxx.trycloudflare.com
"""
import sys
import json
import urllib.request

if len(sys.argv) < 2:
    sys.exit("Kullanim: python test_endpoint.py https://<tunnel>.trycloudflare.com")

BASE = sys.argv[1].rstrip("/")


def get(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer dummy"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer dummy"},
    )
    return json.load(urllib.request.urlopen(req, timeout=120))


# 1) model adi
model = get("/v1/models")["data"][0]["id"]
print(f"✅ Endpoint ayakta. Model: {model}\n")

# 2) sohbet
r = post("/v1/chat/completions", {
    "model": model,
    "messages": [{"role": "user", "content": "Sadece 'merhaba' yaz."}],
})
print("Sohbet yaniti:", r["choices"][0]["message"]["content"].strip(), "\n")

# 3) tool-calling
r = post("/v1/chat/completions", {
    "model": model,
    "messages": [{"role": "user", "content": "Istanbul'da hava nasil? get_weather aracini cagir."}],
    "tools": [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Bir sehrin hava durumunu getirir",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }],
})
msg = r["choices"][0]["message"]
if msg.get("tool_calls"):
    fc = msg["tool_calls"][0]["function"]
    print(f"✅ TOOL-CALLING CALISIYOR -> {fc['name']}({fc['arguments']})")
    print("   Coding agent (Aider/OpenHands) duzgun calisacak.")
else:
    print("⚠️  TOOL-CALLING YOK. Model dogrudan metin dondu:")
    print("   ", (msg.get("content") or "").strip()[:200])
    print("   -> serve.py'de --enable-auto-tool-choice ve dogru --tool-call-parser var mi kontrol et.")
