#!/usr/bin/env bash
# Aider'i Colab'daki Qwen3-Coder endpoint'ine baglar.
# Aider LOKALDE calisir: dosyalari senin makinende olusturur/duzenler, testleri burada kosturur.
#
# Kurulum (bir kez):  python -m pip install aider-install && aider-install
# Kullanim:           ./connect.sh https://<tunnel>.trycloudflare.com [proje_dizini]
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Kullanim: ./connect.sh https://<tunnel>.trycloudflare.com [proje_dizini]"
  exit 1
fi

export OPENAI_API_BASE="${1%/}/v1"
export OPENAI_API_KEY="dummy"

# Model adi, vLLM'in serve ettigi isimle (HF yolu) AYNI olmali. openai/ on eki sart.
MODEL="${MODEL:-openai/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8}"
PROJECT="${2:-.}"

echo "Endpoint : $OPENAI_API_BASE"
echo "Model    : $MODEL"
echo "Proje    : $PROJECT"
cd "$PROJECT"

# --auto-test istersen kendi test komutunu ekle: --test-cmd "pytest -q"
aider --model "$MODEL"
