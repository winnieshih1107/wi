import streamlit as st
import streamlit.components.v1 as components
import pathlib
import json

st.set_page_config(
    page_title="NVIDIA Cosmos 3 Super - AI Image Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome for a full-page experience
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
    [data-testid="stAppViewContainer"] > .main {padding: 0;}
</style>
""", unsafe_allow_html=True)

# Read API keys from Streamlit Secrets (set in Streamlit Cloud dashboard)
gemini_key = ""
hf_token = ""
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    hf_token = st.secrets.get("HF_TOKEN", "")
except Exception:
    pass

# Load the self-contained HTML studio (uses CDN assets, no separate build step)
html_path = pathlib.Path(__file__).parent / "studio.html"
html = html_path.read_text(encoding="utf-8")

# Inject API keys as window globals right after <head> so they are available
# before any inline script runs. json.dumps produces safe JS string literals.
key_injection = f"""<script>
  window.__GEMINI_API_KEY__ = {json.dumps(gemini_key)};
  window.__HF_TOKEN__ = {json.dumps(hf_token)};
</script>"""
html = html.replace("<head>", "<head>\n" + key_injection, 1)

# Render the app. The HTML uses only CDN links (Tailwind, FontAwesome, Google
# Fonts) — no local assets to inline, so it works in components.html() as-is.
components.html(html, height=920, scrolling=True)
