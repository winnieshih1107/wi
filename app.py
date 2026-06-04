import streamlit as st
import requests
import base64
import json
from urllib.parse import quote

st.set_page_config(
    page_title="NVIDIA Cosmos 3 Super — AI Image Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── NVIDIA dark theme ────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #080C14 !important;
    color: #e5e7eb;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stAppViewContainer"] > .main { background-color: #080C14; }
[data-testid="stSidebar"] { background-color: #0B0F17; }
section.main > div { padding-top: 0.5rem; }

/* Hide Streamlit chrome */
#MainMenu, header, footer { visibility: hidden; }

/* Inputs */
textarea, input[type="text"] {
    background-color: #0B0F17 !important;
    border: 1px solid #374151 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
}
textarea:focus, input:focus {
    border-color: #76B900 !important;
    box-shadow: 0 0 0 1px #76B900 !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background-color: #0B0F17 !important;
    border: 1px solid #374151 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
}

/* Buttons */
[data-testid="stButton"] > button {
    background: linear-gradient(to right, #76B900, #5e9400) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 0.6rem 1.5rem !important;
    width: 100%;
    transition: all 0.2s;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(to right, #5e9400, #467000) !important;
    transform: scale(0.99);
}

/* Style preset buttons */
button.style-btn {
    background: #1F2937 !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    color: #d1d5db !important;
    font-size: 12px !important;
    padding: 6px 10px !important;
    cursor: pointer;
    width: 100%;
    text-align: left;
    margin-bottom: 4px;
    transition: all 0.2s;
}
button.style-btn:hover {
    border-color: #76B900 !important;
    background: rgba(118,185,0,0.1) !important;
}

/* Cards */
.card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 16px;
    padding: 20px;
}

/* Labels */
.label {
    font-size: 12px;
    font-weight: 600;
    color: #9ca3af;
    margin-bottom: 6px;
}

/* Status tag */
.status-ready   { background:#76B900/10; color:#76B900; }
.status-loading { background:#eab308/10; color:#eab308; }
.status-error   { background:#ef4444/10; color:#ef4444; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: #1F2937 !important;
    border: 1px solid #374151 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    padding: 0.4rem 1rem !important;
    width: auto !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: #76B900 !important;
    color: #76B900 !important;
}

/* Slider */
[data-testid="stSlider"] > div > div > div { background: #76B900 !important; }

/* Divider */
hr { border-color: #1F2937; }

/* History thumbnails */
img.history-thumb {
    border-radius: 8px;
    border: 1px solid #374151;
    cursor: pointer;
    transition: border-color 0.2s;
}
img.history-thumb:hover { border-color: #76B900; }

/* Scrollbar */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#0B0F17; }
::-webkit-scrollbar-thumb { background:#1F2937; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#76B900; }
</style>
""", unsafe_allow_html=True)

# ── Read secrets ─────────────────────────────────────────────────────────────
gemini_key = ""
hf_token   = ""
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    hf_token   = st.secrets.get("HF_TOKEN", "")
except Exception:
    pass

# Pre-fill HF token from secrets into session
if "hf_token" not in st.session_state:
    st.session_state.hf_token = hf_token
if "history" not in st.session_state:
    st.session_state.history = []
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:14px 0 18px;border-bottom:1px solid #1F2937;margin-bottom:20px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#76B900,#467000);
                display:flex;align-items:center;justify-content:center;font-size:18px;">⚡</div>
    <div>
      <div style="font-size:18px;font-weight:800;background:linear-gradient(to right,#fff,#76B900);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;">NVIDIA Cosmos 3</div>
      <div style="font-size:10px;color:#76B900;font-weight:700;letter-spacing:2px;margin-top:-2px;">
        SUPER TEXT-TO-IMAGE STUDIO</div>
    </div>
  </div>
  <div style="display:flex;gap:10px;align-items:center;">
    <span style="font-size:11px;font-weight:700;color:#76B900;padding:4px 10px;
                 border-radius:999px;border:1px solid rgba(118,185,0,0.4);
                 background:rgba(118,185,0,0.08);">● 免 Key 生成已啟用</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Style presets ─────────────────────────────────────────────────────────────
STYLE_PRESETS = {
    "🌃 賽博朋克": "cyberpunk, hyper-detailed neon streets, volumetric holographic advertising, rainy night, cinematic reflections, octane render, 8k",
    "🎬 電影質感": "cinematic still, photorealistic, dramatic movie lighting, depth of field, anamorphic lens, highly textured, incredible realistic details",
    "🌸 唯美動漫": "beautiful anime style illustration, vibrant colors, soft glowing lighting, aesthetic background, masterpiece, Makoto Shinkai style",
    "📸 寫實攝影": "professional studio photography, high-end commercial shot, ultra detailed, sharp focus, real textures, dramatic soft ambient lighting, 8k",
    "🦄 奇幻唯美": "high fantasy concept art, mystical fog, ancient towering glowing tree, ethereal fairies, majestic lighting, magical particles",
    "🎨 水彩手繪": "exquisite fluid watercolor painting, detailed pencil outlines, wet-on-wet technique, delicate pastel splatters, elegant composition",
}

RATIO_MAP = {
    "1:1":  (1024, 1024),
    "16:9": (1024, 576),
    "9:16": (576,  1024),
    "4:3":  (1024, 768),
    "3:4":  (768,  1024),
}

# ── Layout ────────────────────────────────────────────────────────────────────
left, right = st.columns([5, 7], gap="large")

# ════════════════════════════════════════════════════════════════════════════
# LEFT PANEL
# ════════════════════════════════════════════════════════════════════════════
with left:
    # Prompt card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="label">✨ 藝術提示詞 (Prompt)</div>', unsafe_allow_html=True)
    prompt = st.text_area("", placeholder="用英文或中文描繪您的想像...",
                          height=110, key="prompt_input", label_visibility="collapsed")

    # Style preset buttons (2 rows × 3)
    st.markdown('<div class="label" style="margin-top:12px;">風格預設快速鍵</div>', unsafe_allow_html=True)
    rows = [list(STYLE_PRESETS.items())[i:i+3] for i in range(0, 6, 3)]
    for row in rows:
        cols = st.columns(3)
        for col, (label, style_str) in zip(cols, row):
            if col.button(label, key=f"style_{label}"):
                current = st.session_state.get("prompt_input", "")
                st.session_state.prompt_input = (current + ", " + style_str).lstrip(", ")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Engine & params card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="label">⚙️ 生成模型與參數</div>', unsafe_allow_html=True)

    engine = st.selectbox("生成引擎 (Engine Mode)", [
        "🆓 完全免費生成 (Pollinations FLUX)",
        "✨ Gemini 2.0 Flash 圖像生成 (免費 Gemini Key 可用)",
        "🚀 NVIDIA Cosmos 3 Super (需要 HF Token)",
        "⚡ FLUX.1 Schnell (需要 HF Token)",
        "🌌 Stable Diffusion XL (需要 HF Token)",
    ], label_visibility="collapsed")

    engine_key = engine.split("(")[0].strip()

    ratio = st.radio("畫面比例", list(RATIO_MAP.keys()), horizontal=True)

    is_hf = "HF Token" in engine
    is_free = "Pollinations" in engine

    with st.expander("進階參數（HF 模型專用）", expanded=is_hf):
        neg_prompt = st.text_input("負面提示詞", value="low quality, blurry, deformed, bad anatomy, text, watermark")
        c1, c2 = st.columns(2)
        cfg = c1.slider("引導係數 (CFG)", 1.0, 20.0, 7.0, 0.5)
        steps = c2.slider("生成步數 (Steps)", 10, 60, 28)
        hf_tok = st.text_input("Hugging Face Token", value=st.session_state.hf_token,
                               type="password", placeholder="hf_xxxxxxxxxxxx")
        st.session_state.hf_token = hf_tok

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    gen_btn = st.button("⚡ 啟動大師級繪畫生成", use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL
# ════════════════════════════════════════════════════════════════════════════
with right:
    # Main display card
    st.markdown('<div class="card" style="min-height:480px;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;
                border-bottom:1px solid #1F2937;padding-bottom:10px;margin-bottom:14px;">
      <span style="font-size:12px;font-weight:700;color:#9ca3af;display:flex;align-items:center;gap:6px;">
        <span style="width:8px;height:8px;border-radius:50%;background:#76B900;display:inline-block;"></span>
        生成主控台
      </span>
      <span id="status-tag" style="font-size:11px;font-weight:700;color:#76B900;
            padding:2px 10px;border-radius:999px;background:rgba(118,185,0,0.08);">準備就緒</span>
    </div>
    """, unsafe_allow_html=True)

    img_placeholder = st.empty()
    meta_placeholder = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

    # History gallery
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    hist_header = st.columns([8, 2])
    hist_header[0].markdown(f'<div class="label">🖼️ 個人藝術歷史廊 ({len(st.session_state.history)})</div>',
                            unsafe_allow_html=True)
    if hist_header[1].button("清除", key="clear_hist"):
        st.session_state.history = []
        st.rerun()

    if st.session_state.history:
        cols = st.columns(min(len(st.session_state.history), 4))
        for i, item in enumerate(st.session_state.history[:4]):
            with cols[i]:
                st.image(item["image"], use_container_width=True)
                st.caption(item["prompt"][:30] + "…" if len(item["prompt"]) > 30 else item["prompt"])
    else:
        st.markdown('<div style="text-align:center;padding:24px;color:#4b5563;font-size:13px;">'
                    '尚無生成紀錄，啟動您的第一次創作吧！</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Show current image (persisted across reruns)
if st.session_state.current_image:
    with img_placeholder:
        st.image(st.session_state.current_image, use_container_width=True)
    with meta_placeholder:
        st.caption(f"Prompt: {st.session_state.current_prompt}")
        st.download_button("⬇ 下載圖片", data=st.session_state.current_image,
                           file_name="cosmos3-generation.png", mime="image/png")
else:
    with img_placeholder:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#6b7280;">
          <div style="font-size:40px;margin-bottom:12px;">🖼️</div>
          <div style="font-weight:700;color:#d1d5db;margin-bottom:6px;">智慧繪圖生成區</div>
          <div style="font-size:13px;">目前已啟用免密鑰模式，直接在左方輸入 Prompt 後按下「啟動」按鈕即可生成。</div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# GENERATION LOGIC (server-side, no CORS issues)
# ════════════════════════════════════════════════════════════════════════════
if gen_btn:
    raw_prompt = st.session_state.get("prompt_input", "").strip()
    if not raw_prompt:
        st.warning("請輸入提示詞！")
        st.stop()

    w, h = RATIO_MAP[ratio]
    image_bytes = None

    with st.spinner("正在生成圖像，請稍候..."):
        try:
            if is_free:
                import random, time

                # ── 方案 A：HF FLUX.1-schnell 免 Token ───────────────────
                image_bytes = None
                hf_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
                try:
                    hf_resp = requests.post(
                        hf_url,
                        json={"inputs": raw_prompt},
                        headers={"Content-Type": "application/json"},
                        timeout=90,
                    )
                    if hf_resp.ok and hf_resp.headers.get("content-type","").startswith("image"):
                        image_bytes = hf_resp.content
                except Exception:
                    pass

                # ── 方案 B：Pollinations（重試 3 次，每次間隔 6 秒）──────
                if not image_bytes:
                    seed = random.randint(0, 999999)
                    poll_url = (f"https://image.pollinations.ai/prompt/{quote(raw_prompt)}"
                                f"?width={w}&height={h}&seed={seed}&model=flux")
                    for attempt in range(3):
                        try:
                            poll_resp = requests.get(poll_url, timeout=60)
                            if poll_resp.ok:
                                image_bytes = poll_resp.content
                                break
                            if poll_resp.status_code == 402 and attempt < 2:
                                time.sleep(6)
                                continue
                            poll_resp.raise_for_status()
                        except requests.HTTPError:
                            if attempt == 2:
                                raise
                            time.sleep(6)

                if not image_bytes:
                    st.error(
                        "免費伺服器目前忙碌（IP 排隊已滿）。建議：\n\n"
                        "1. 稍等 10 秒後再點擊生成\n"
                        "2. 或至 [aistudio.google.com](https://aistudio.google.com/apikey) "
                        "取得免費 Gemini API Key，在 Streamlit Secrets 設定 `GEMINI_API_KEY`，"
                        "改用 Imagen 4.0 引擎（更穩定）"
                    )
                    st.stop()

            elif "Gemini" in engine:
                # ── Gemini Image Generation（依序嘗試可用模型）──────────
                active_key = gemini_key
                if not active_key:
                    st.error("請在 Streamlit Secrets 中設定 GEMINI_API_KEY\n\n"
                             "免費申請：https://aistudio.google.com/apikey")
                    st.stop()

                # 只選一個最佳模型，避免連環嘗試耗盡每日配額
                # 優先順序：gemini-2.5-flash-image > gemini-3.1-flash-image-preview > gemini-3.1-flash-image
                PREFERRED = [
                    "gemini-2.5-flash-image",
                    "gemini-3.1-flash-image-preview",
                    "gemini-3.1-flash-image",
                    "gemini-3-pro-image-preview",
                ]

                image_bytes = None
                used_model = None
                last_status = 0
                last_msg = ""

                for model_name in PREFERRED:
                    ep = (
                        "https://generativelanguage.googleapis.com/v1beta/models"
                        f"/{model_name}:generateContent?key={active_key}"
                    )
                    payload = {
                        "contents": [{"parts": [{"text": raw_prompt}]}],
                        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
                    }
                    r = requests.post(ep, json=payload, timeout=60)
                    last_status = r.status_code
                    last_msg = r.text[:300]

                    if r.status_code == 429:
                        # Quota 超過 → 不要繼續試其他模型（會繼續消耗配額）
                        st.error(
                            "**每日免費配額已用盡（429 Quota Exceeded）**\n\n"
                            "免費 Gemini API 圖像生成每日有限制次數，今日已達上限。\n\n"
                            "**解決方法：**\n"
                            "- ⏰ 等待到明天配額重置後再試\n"
                            "- 🔄 現在改用「**🆓 完全免費生成 (Pollinations FLUX)**」引擎（不消耗 Gemini 配額）\n"
                            "- 💳 至 [Google AI Studio](https://aistudio.google.com) 升級付費方案獲得更高配額"
                        )
                        st.stop()

                    if r.status_code == 404:
                        continue  # 此模型不存在，試下一個

                    if not r.ok:
                        st.error(f"Gemini API 錯誤 ({r.status_code})：{last_msg}")
                        st.stop()

                    # 成功：取出圖像
                    for part in (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            image_bytes = base64.b64decode(part["inlineData"]["data"])
                            used_model = model_name
                            break
                    if image_bytes:
                        break

                if not image_bytes:
                    st.error(
                        f"所有 Gemini 圖像模型均回傳 404（不可用）。\n"
                        "請改用「🆓 完全免費生成 (Pollinations FLUX)」引擎。"
                    )
                    st.stop()

            else:
                # ── Hugging Face Inference API ────────────────────────────
                tok = st.session_state.hf_token.strip()
                if not tok:
                    st.error("請輸入 Hugging Face Token！")
                    st.stop()
                model_id_map = {
                    "🚀 NVIDIA Cosmos 3 Super": "nvidia/Cosmos3-Super-Text2Image",
                    "⚡ FLUX.1 Schnell":         "black-forest-labs/FLUX.1-schnell",
                    "🌌 Stable Diffusion XL":    "stabilityai/stable-diffusion-xl-base-1.0",
                }
                model_id = next((v for k, v in model_id_map.items() if k in engine), "")
                payload = {
                    "inputs": raw_prompt,
                    "parameters": {
                        "negative_prompt": neg_prompt,
                        "guidance_scale": cfg,
                        "num_inference_steps": steps,
                        "width": w, "height": h,
                    }
                }
                resp = requests.post(
                    f"https://api-inference.huggingface.co/models/{model_id}",
                    headers={"Authorization": f"Bearer {tok}"},
                    json=payload, timeout=120
                )
                resp.raise_for_status()
                image_bytes = resp.content

        except requests.HTTPError as e:
            st.error(f"API 錯誤 ({e.response.status_code})：{e.response.text[:200]}")
            st.stop()
        except Exception as e:
            st.error(f"生成失敗：{e}")
            st.stop()

    if image_bytes:
        st.session_state.current_image = image_bytes
        st.session_state.current_prompt = raw_prompt
        st.session_state.history.insert(0, {"image": image_bytes, "prompt": raw_prompt})
        if len(st.session_state.history) > 8:
            st.session_state.history = st.session_state.history[:8]
        st.rerun()
