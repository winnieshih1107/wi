# NVIDIA Cosmos 3 Super — AI Image Studio

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://wicosmos3.streamlit.app)

**Live Demo → https://wicosmos3.streamlit.app**

A premium AI text-to-image web application with NVIDIA dark-theme UI, supporting multiple free and professional generation engines.

---

## Engines

| Engine | API Key Required | Speed |
|--------|-----------------|-------|
| 🆓 **Pollinations FLUX** (default) | None | ~15s |
| ✨ Google Imagen 4.0 | Gemini API Key | ~10s |
| 🚀 NVIDIA Cosmos 3 Super (64B) | HF Token | ~30s |
| ⚡ FLUX.1 Schnell | HF Token | ~20s |
| 🌌 Stable Diffusion XL | HF Token | ~20s |

## Features

- Zero-config free generation via Pollinations.ai FLUX
- Gemini 2.5 Flash AI prompt expansion
- 6 style presets (Cyberpunk / Cinematic / Anime / Realism / Fantasy / Watercolor)
- 5 aspect ratios (1:1 / 16:9 / 9:16 / 4:3 / 3:4)
- CFG scale, inference steps, seed control
- Generation history gallery + download

---

## Deploy to Streamlit Cloud

1. Fork this repo
2. Go to https://share.streamlit.io → **New app**
3. Select your fork, branch `main`, main file `app.py`
4. *(Optional)* Add secrets under **App Settings → Secrets**:

```toml
GEMINI_API_KEY = "your-gemini-key"   # enables Imagen 4.0 + AI prompt expand
HF_TOKEN       = "hf_xxxxxxxxxxxx"   # enables Cosmos 3 / FLUX / SDXL
```

5. Click **Deploy** — the free Pollinations engine works without any secrets.

---

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

For optional secret keys, create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-gemini-key"
HF_TOKEN       = "hf_xxxxxxxxxxxx"
```

---

## Architecture

```
Streamlit (app.py)
  ├── reads GEMINI_API_KEY / HF_TOKEN from st.secrets
  ├── injects them as window.__GEMINI_API_KEY__ / __HF_TOKEN__
  └── serves studio.html via st.components.v1.html()
        ↓
  Self-contained HTML (Tailwind CDN + Vanilla JS)
        ├── Pollinations FLUX  →  image.pollinations.ai  (free, no auth)
        ├── Gemini Imagen 4.0  →  generativelanguage.googleapis.com
        └── HF Inference API   →  api-inference.huggingface.co
```

## Project Structure

```
cosmos3-image-studio/
├── app.py              # Streamlit entry — injects secrets, serves HTML
├── studio.html         # Self-contained NVIDIA-styled UI (CDN assets)
├── requirements.txt    # streamlit
└── .streamlit/
    └── config.toml
```
