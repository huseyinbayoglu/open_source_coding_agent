#!/usr/bin/env python3
"""
Qwen3-Coder'i Colab'da coding-agent BEYNI olarak servis eder.

vLLM (tool-calling acik) + cloudflared tuneli -> public https endpoint.
Cikan adresi lokalde Aider/OpenHands'e baglarsin. Dosya islemleri LOKALDE olur;
burada sadece model "dusunur" (token uretir).

Kullanim (Colab):
    !python serve.py

Ozellestir (GPU'na gore -> README tablosu):
    !MODEL="Qwen/Qwen2.5-Coder-14B-Instruct-AWQ" TOOL_PARSER=hermes EXTRA_ARGS="--quantization awq" python serve.py
"""
import os
import re
import sys
import time
import shutil
import subprocess
import urllib.request

CONFIG = {
    "MODEL":       os.environ.get("MODEL", "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"),  # A100 40GB
    "TOOL_PARSER": os.environ.get("TOOL_PARSER", "qwen3_coder"),   # Qwen2.5-Coder icin: hermes
    "MAX_LEN":     os.environ.get("MAX_LEN", "32768"),
    "GPU_UTIL":    os.environ.get("GPU_UTIL", "0.92"),
    "PORT":        os.environ.get("PORT", "8000"),
    "EXTRA_ARGS":  os.environ.get("EXTRA_ARGS", ""),               # ornek AWQ: "--quantization awq"
}


def sh(cmd):
    print(f"$ {cmd}", flush=True)
    subprocess.run(cmd, shell=True, check=True)


def ensure_deps():
    """vLLM ve cloudflared kurulu degilse kur."""
    try:
        import vllm  # noqa: F401
        print(f"vLLM zaten kurulu: {vllm.__version__}")
    except Exception:
        # PyPI'daki varsayilan vLLM wheel'i artik CUDA 13 ile geliyor; Colab'da CUDA 12 var.
        # uv + --torch-backend=auto ortamdaki CUDA'yi tespit edip uyumlu wheel'i kurar
        # (vLLM'in resmi onerdigi yontem). Boylece "libcudart.so.13" hatasi olmaz.
        sh("pip install -q -U uv")
        sh("uv pip install --system -q vllm --torch-backend=auto")
    if shutil.which("cloudflared") is None:
        sh("wget -q https://github.com/cloudflare/cloudflared/releases/latest/"
           "download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb")
        sh("dpkg -i /tmp/cloudflared.deb")
    else:
        print("cloudflared zaten kurulu.")


def start_vllm():
    c = CONFIG
    cmd = [
        "vllm", "serve", c["MODEL"],
        "--enable-auto-tool-choice",
        "--tool-call-parser", c["TOOL_PARSER"],
        "--max-model-len", c["MAX_LEN"],
        "--gpu-memory-utilization", c["GPU_UTIL"],
        "--port", c["PORT"],
    ]
    if c["EXTRA_ARGS"].strip():
        cmd += c["EXTRA_ARGS"].split()
    print("vLLM baslatiliyor:\n  " + " ".join(cmd), flush=True)
    log = open("vllm.log", "w")
    return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)


def wait_until_ready(proc, port):
    url = f"http://localhost:{port}/v1/models"
    while True:
        try:
            urllib.request.urlopen(url, timeout=3)
            return
        except Exception:
            if proc.poll() is not None:
                tail = "".join(open("vllm.log").readlines()[-40:])
                print("\n--- vllm.log (son 40 satir) ---\n" + tail, flush=True)
                sys.exit("vLLM coktu. Cogu zaman sebep OOM -> daha kucuk MODEL veya MAX_LEN dene.")
            print("  ...model indiriliyor/yukleniyor", flush=True)
            time.sleep(10)


def start_tunnel(port):
    """cloudflared'i on planda calistirir, public URL'yi yakalayip basar, oturumu canli tutar."""
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    printed = False
    for line in proc.stdout:
        print(line, end="", flush=True)
        m = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", line)
        if m and not printed:
            printed = True
            url = m.group(0)
            print("\n" + "=" * 70)
            print("ENDPOINT HAZIR  ✅   (bu hucre acik kaldigi surece calisir)")
            print(f"  Endpoint : {url}/v1")
            print(f"  Model    : openai/{CONFIG['MODEL']}")
            print("\n  Lokalde test:  python local/test_endpoint.py " + url)
            print("  Lokalde agent: ./local/connect.sh " + url)
            print("=" * 70 + "\n", flush=True)
    proc.wait()


def main():
    ensure_deps()
    vllm = start_vllm()
    wait_until_ready(vllm, CONFIG["PORT"])
    print("✅ vLLM hazir. Tunel aciliyor...", flush=True)
    start_tunnel(CONFIG["PORT"])


if __name__ == "__main__":
    main()
