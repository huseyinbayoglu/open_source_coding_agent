# open_source_coding_agent

Kendi açık kaynak LLM'ini (Qwen3-Coder) **Colab'da** servis edip, **lokal makinende** Claude Code / Codex
benzeri bir coding agent'ın beyni olarak kullanmak için minimal kurulum.

## Nasıl çalışır? (en önemli kısım)

Dosyalar **senin makinende** değişir, Colab'da değil. Colab sadece "düşünür".

```
Senin Mac'in (LOKAL)                      Colab (UZAK / GPU)
┌──────────────────────────┐   https   ┌────────────────────────┐
│  Aider (veya OpenHands)   │  tünel    │  Qwen3-Coder (vLLM)    │
│  • dosya okur / yazar     │ ◄───────► │  • sadece token üretir │
│  • mkdir, test çalıştırır │  (metin)  │  • tool-calling üretir │
│  • git commit             │           │                        │
└──────────────────────────┘           └────────────────────────┘
```

- Tünelden **sadece sohbet mesajları** geçer (OpenAI uyumlu `/v1/chat/completions`). Kod/dosya gönderilmez.
- Beyin "şu dosyayı oluştur / `mkdir` / testi çalıştır" der → **Aider bunu senin Mac'inde uygular.**
- Yani: *Colab karar verir, lokalinde çalışır.*

## Bileşenler

| Dosya | Nerede çalışır | Ne yapar |
|---|---|---|
| `colab/serve.py` | Colab | Qwen3-Coder'ı vLLM (tool-calling açık) + cloudflared tüneliyle servis eder |
| `local/test_endpoint.py` | Lokal | Endpoint'i ve **tool-calling'i** test eder (agent'tan önce mutlaka çalıştır) |
| `local/connect.sh` | Lokal | Aider'ı endpoint'e bağlar |
| `local/.env.example` | Lokal | Ortam değişkeni şablonu |

---

## Adım adım

### 1) Repoyu Colab'da aç ve modeli servis et

Yeni bir Colab notebook'ta (Çalışma zamanı → **GPU** seçili):

```python
!git clone https://github.com/huseyinbayoglu/open_source_coding_agent.git
%cd open_source_coding_agent
!python colab/serve.py
```

Son hücre **açık kalmalı** (oturumu canlı tutar). Hazır olunca şuna benzer bir çıktı basar:

```
ENDPOINT HAZIR  ✅
  Endpoint : https://random-words.trycloudflare.com/v1
  Model    : openai/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
```

Bu URL'yi kopyala. (Colab her kapanıp açıldığında **URL değişir**.)

### 2) Lokalde endpoint'i test et (agent'tan önce!)

```bash
python local/test_endpoint.py https://random-words.trycloudflare.com
```

Çıktıda **`✅ TOOL-CALLING CALISIYOR`** görmen lazım. Görmüyorsan agent düzgün çalışmaz
(aşağıdaki Sorun Giderme'ye bak).

### 3) Aider'ı bağla

Bir kez kurulum:
```bash
python -m pip install aider-install && aider-install
```

Bağlan (düzenlemek istediğin projenin dizinini ver):
```bash
chmod +x local/connect.sh
./local/connect.sh https://random-words.trycloudflare.com /path/to/projen
```

Artık Aider içinde "auth.py'deki bug'ı düzelt", "şu testi geçecek şekilde yeni bir endpoint ekle"
gibi şeyler isteyebilirsin; dosyaları lokalde değiştirir, `git diff` gösterir, istersen testleri çalıştırır.

---

## GPU'na göre model seçimi

Colab'ın verdiği GPU'ya göre `serve.py` çağrısını değiştir (VRAM'e sığması için):

| Colab GPU | VRAM | MODEL | TOOL_PARSER | Ek |
|---|---|---|---|---|
| A100 (Pro+) | 40 GB | `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | `qwen3_coder` | (varsayılan) |
| L4 | 24 GB | `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | `hermes` | `EXTRA_ARGS="--quantization awq"` |
| T4 | 16 GB | `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` | `hermes` | `EXTRA_ARGS="--quantization awq"` |

Örnek (L4):
```python
!MODEL="Qwen/Qwen2.5-Coder-14B-Instruct-AWQ" TOOL_PARSER=hermes EXTRA_ARGS="--quantization awq" \
  python colab/serve.py
```

> `connect.sh`'de de `MODEL` değişkenini servis ettiğin isimle aynı yap:
> `MODEL=openai/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ ./local/connect.sh <url> <proje>`

---

## Daha fazla "tool" / daha otonom istiyorsan: OpenHands

Aider düzenleme odaklıdır ve hızlı başlamak için idealdir. Modelin kendi başına terminal kullanması,
çok adımlı otonom döngü (Claude Code'a daha yakın) istersen **OpenHands** kullan — aynı Colab endpoint'ine bağlanır:

```bash
docker run -it --rm --pull=always \
  -e LLM_BASE_URL="https://random-words.trycloudflare.com/v1" \
  -e LLM_API_KEY="dummy" \
  -e LLM_MODEL="openai/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  -v "$PWD:/workspace" \
  -p 3000:3000 \
  docker.all-hands.dev/all-hands-ai/openhands:latest
```

OpenHands tool-calling'e Aider'dan daha bağımlıdır → önce `test_endpoint.py` ile tool-calling'i doğrula.

---

## Sorun Giderme

- **vLLM çöküyor / OOM:** Model VRAM'e sığmıyor. Tablodan daha küçük model seç ya da `MAX_LEN=8192` ver.
- **`test_endpoint.py` tool-calling göstermiyor:** `serve.py`'de `--enable-auto-tool-choice` var mı ve
  `TOOL_PARSER` modele uygun mu? (Qwen3-Coder → `qwen3_coder`, Qwen2.5-Coder → `hermes`). vLLM'i güncelle.
- **Aider "model bilinmiyor" uyarısı:** Zararsız; context limiti uyarısıdır, çalışmaya devam eder.
- **URL'ye bağlanamıyorum:** Colab'daki `serve.py` hücresi hâlâ açık mı? Tünel kapanınca URL ölür.
- **Yavaş:** Tek GPU + tünel gecikmesi normaldir. Geliştirme/test için yeterli; üretim hedefi değil.

## Notlar

- Colab oturumu birkaç saat sonra kapanır → endpoint ölür, yeniden açınca **URL değişir**. Sadece dev/test için.
- Tünel public'tir ama URL tahmin edilemez; yine de hassas bir şey servis etme.
- Kararlı/uzun kullanım istersen ileride RunPod / Vast.ai (saatlik GPU) + sabit endpoint'e geçebilirsin.
