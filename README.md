# open_source_coding_agent

Kendi açık kaynak LLM'ini (Qwen3-Coder) **Colab'da** servis edip, **lokal makinende** Claude Code / Codex
benzeri bir coding agent'ın beyni olarak kullan. Ajan **OpenHands**; beyin **senin Qwen3-Coder'ın**.

## Nasıl çalışır? (en önemli kısım)

Dosyalar **senin makinende** değişir, Colab'da değil. Colab sadece "düşünür".

```
Senin Mac'in (LOKAL)                      Colab (UZAK / GPU)
┌──────────────────────────┐   https   ┌────────────────────────┐
│  OpenHands (Docker)       │  tünel    │  Qwen3-Coder (vLLM)    │
│  • projeyi keşfeder       │ ◄───────► │  • sadece token üretir │
│  • dosya oluştur/sil/yaz  │  (metin)  │  • tool-calling üretir │
│  • bash, test, python     │           │                        │
│  • git                    │           │                        │
└──────────────────────────┘           └────────────────────────┘
```

- Tünelden **sadece sohbet mesajları** geçer (OpenAI uyumlu `/v1/chat/completions`). Kod/dosya gitmez.
- Beyin "şu dosyayı oluştur / `mkdir` / testi çalıştır" der → **OpenHands bunu senin Mac'inde uygular.**
- Toolları (bash, dosya editörü, kod yazma, Python, browser) **OpenHands hazır getirir** — sen vermezsin.
  Sen sadece **rol/skill** dosyalarını (microagents) yazarsın.

## Bileşenler

| Dosya | Nerede | Ne yapar |
|---|---|---|
| `colab/serve.py` | Colab | Qwen3-Coder'ı vLLM (tool-calling açık) + cloudflared tüneliyle servis eder |
| `local/test_endpoint.py` | Lokal | Endpoint + **tool-calling** testi (ajandan önce mutlaka çalıştır) |
| `openhands/start_openhands.sh` | Lokal | OpenHands'i Docker ile başlatır (GUI: localhost:3000) |
| `openhands/microagents-template/` | Lokal | Rol (`repo.md`) ve skill (`knowledge/*.md`) şablonları |
| `local/connect.sh` | Lokal | (Opsiyonel) Aider ile 2 dakikalık hızlı endpoint denemesi |

---

## Adım adım

### 1) Colab'da modeli servis et

GPU'lu yeni bir Colab notebook'ta:

```python
!git clone https://github.com/huseyinbayoglu/open_source_coding_agent.git
%cd open_source_coding_agent
!python colab/serve.py
```

Bu hücre **açık kalmalı**. Hazır olunca `https://...trycloudflare.com` URL'sini basar. Kopyala.
(Colab her açıldığında **URL değişir**.)

### 2) Endpoint'i ve tool-calling'i test et (ajandan önce!)

```bash
python local/test_endpoint.py https://xxxx.trycloudflare.com
```

Çıktıda **`✅ TOOL-CALLING CALISIYOR`** görmelisin. Görmüyorsan OpenHands düzgün çalışmaz
(aşağıdaki Sorun Giderme'ye bak).

### 3) OpenHands'i başlat

Docker Desktop kurulu ve çalışır olmalı. Sonra:

```bash
chmod +x openhands/start_openhands.sh
./openhands/start_openhands.sh
```

Tarayıcıda **http://localhost:3000** açılır.

> Not: OpenHands sürüm etiketleri hızlı değişir. Script çalışmazsa güncel `docker run` komutunu
> <https://docs.openhands.dev> "Setup" sayfasından alıp `OH_VERSION` / `AGENT_SERVER_TAG`'i güncelle.

### 4) UI'dan Colab endpoint'ini bağla

OpenHands arayüzünde **Settings (dişli) → LLM → Advanced** aç ve şunları gir:

| Alan | Değer |
|---|---|
| Custom Model | `openai/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` |
| Base URL | `https://xxxx.trycloudflare.com/v1` |
| API Key | `dummy` (herhangi bir şey) |

> Endpoint public bir https adresi olduğu için `host.docker.internal`'a gerek yok; container doğrudan erişir.
> Colab'ı her yeniden açtığında **Base URL'yi güncellemen** gerekir (tünel URL'si değişir).

### 5) Projeyi aç ve kullan

OpenHands UI'dan üzerinde çalışacağın projeyi/repoyu aç. Artık:

> "Projeye bak, eksik olan input validation'ı tespit et ve gerekli dosyaları oluşturup yaz, sonra testleri çalıştır."

gibi görevler verebilirsin. OpenHands keşfeder → eksikleri bulur → dosya oluşturur/kod yazar → test çalıştırır → düzeltir.

---

## Rol ve skill verme (microagents)

OpenHands rol/kural/skill'leri **çalıştığın projenin içinden** okur: `<projen>/.openhands/microagents/`.
Bu repodaki şablonları oraya kopyala:

```bash
mkdir -p /path/to/projen/.openhands/microagents/knowledge
cp openhands/microagents-template/repo.md            /path/to/projen/.openhands/microagents/
cp openhands/microagents-template/knowledge/testing.md /path/to/projen/.openhands/microagents/knowledge/
```

- **`repo.md`** → frontmatter yok = **her sohbette otomatik yüklenir.** Ajanın kalıcı "rolü" ve proje
  kuralları (Claude Code'daki `CLAUDE.md` karşılığı). İçindeki "Bu proje hakkında" kısmını doldur.
- **`knowledge/*.md`** → frontmatter'da `triggers: [test, pytest]` → o kelimeler geçince yüklenen **skill**
  (Claude Code'daki skill mantığı). İhtiyacına göre çoğalt: `deploy.md`, `db.md`, `frontend.md` ...

---

## GPU'na göre model seçimi

`serve.py` çağrısını Colab'ın verdiği GPU'ya göre değiştir (VRAM'e sığması için):

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
> Modeli değiştirirsen UI'daki **Custom Model** alanını da aynı isimle güncelle (`openai/...` ön ekiyle).

---

## Aider (düşük bant genişliği / hafif alternatif)

OpenHands ~2–4 GB Docker imajı indirir. İnternetin kısıtlıysa **Aider** çok daha hafiftir (~150–300 MB, Docker yok)
ve coding-agent işini görür: keşfet, düzenle, **yeni dosya oluştur**, test çalıştır, git.

```bash
python -m pip install aider-install && aider-install
./local/connect.sh https://xxxx.trycloudflare.com /path/to/projen
```

### Aider'ı kişiselleştir (rol + otomatik test)
OpenHands kadar olmasa da Aider epey ayarlanabilir. Şablonları projenin köküne kopyala:
```bash
cp local/CONVENTIONS.md       /path/to/projen/CONVENTIONS.md       # rol/kurallar (repo.md karşılığı)
cp local/aider.conf.yml.example /path/to/projen/.aider.conf.yml    # auto-test, read, map ayarları
```
- `CONVENTIONS.md` → her sohbette yüklenen kalıcı rol/stil. İçindeki "Bu proje hakkında"yı doldur.
- `.aider.conf.yml` → `auto-test`/`test-cmd` ile testi otomatik çalıştırıp düzeltir, `read` ile conventions'ı ekler.

**OpenHands'e göre eksiği:** tetiklenen çoklu skill sistemi (`knowledge/*.md` + triggers) ve tam otonom ajan döngüsü
yok. Rol, stil, otomatik test, dosya/komut çalıştırma ise Aider'da da var.

---

## Sorun Giderme

- **`ImportError: libcudart.so.13` (veya .so.12):** vLLM ile torch farklı CUDA sürümünde. `serve.py` artık
  `uv pip install --system --reinstall vllm --torch-backend=auto` ile kurar (`--reinstall` torch'u da
  eşitler). Elle temizlemek için: `pip uninstall -y vllm && pip install -U uv && uv pip install --system --reinstall vllm --torch-backend=auto`,
  sonra **Runtime → Restart session**. Doğrulama: `python -c "import vllm._C; print('ok')"` (sadece `import vllm` yanıltıcı — `_C`'yi test et).
- **vLLM çöküyor / OOM:** Model VRAM'e sığmıyor → daha küçük model seç ya da `MAX_LEN=8192` ver.
- **`test_endpoint.py` tool-calling göstermiyor:** `serve.py`'de `--enable-auto-tool-choice` var mı,
  `TOOL_PARSER` modele uygun mu? (Qwen3-Coder→`qwen3_coder`, Qwen2.5-Coder→`hermes`). vLLM'i güncelle.
- **OpenHands başlamıyor:** Docker Desktop açık mı? İmaj tag'leri eski olabilir → docs'tan güncel komutu al.
- **OpenHands modele bağlanamıyor:** Base URL sonunda `/v1` var mı? Colab hücresi hâlâ açık mı? URL değişti mi?
- **Yavaş:** Tek GPU + tünel gecikmesi normaldir. Dev/test için yeterli; üretim hedefi değil.

## Notlar

- Colab oturumu birkaç saat sonra kapanır → endpoint ölür, yeniden açınca **URL değişir** (UI'da güncelle).
- Tünel public'tir ama URL tahmin edilemez; yine de hassas bir şey servis etme.
- Kararlı/uzun kullanım istersen ileride RunPod / Vast.ai (saatlik GPU) + sabit endpoint'e geçebilirsin.

## Kaynaklar

- OpenHands: <https://github.com/OpenHands/OpenHands> · Docs: <https://docs.openhands.dev>
- Microagents/skills: <https://docs.openhands.dev/usage/customization/microagents-overview>
