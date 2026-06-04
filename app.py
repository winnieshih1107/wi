import streamlit as st
import streamlit.components.v1 as components
import pathlib
import re
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

dist_path = pathlib.Path(__file__).parent / "dist"

if not dist_path.exists():
    st.error(
        "**Build files not found.**\n\n"
        "Run `npm run build` inside the `cosmos-studio/` directory first, "
        "then commit the generated `dist/` folder.",
        icon="🚨"
    )
    st.code("npm run build", language="bash")
    st.stop()

html = (dist_path / "index.html").read_text(encoding="utf-8")

# Fix the default Vite title
html = html.replace(
    "<title>Vite + React + TS</title>",
    "<title>NVIDIA Cosmos 3 Super - AI Image Studio</title>"
)

# Inject API keys as window globals BEFORE any script runs.
# Using json.dumps produces valid JS string literals and handles escaping.
key_injection = f"""<script>
  window.__GEMINI_API_KEY__ = {json.dumps(gemini_key)};
  window.__HF_TOKEN__ = {json.dumps(hf_token)};
</script>"""

# Insert key injection right after <head> so it runs before module scripts.
html = html.replace("<head>", "<head>\n" + key_injection, 1)

# Inline all JS assets referenced in the HTML.
# components.html() renders inside a sandboxed iframe — relative src paths like
# ./assets/index-xxx.js cannot be fetched from there, so we embed the file content.
def _inline_script(match: re.Match) -> str:
    src = match.group(1)                       # e.g. "./assets/index-abc.js"
    rel = src.lstrip("./")                     # e.g.  "assets/index-abc.js"
    js_path = dist_path / rel
    if js_path.exists():
        content = js_path.read_text(encoding="utf-8")
        return f'<script type="module">{content}</script>'
    return match.group(0)                      # leave unchanged if not found

html = re.sub(
    r'<script\b[^>]*\bsrc="(\./[^"]+\.js)"[^>]*/?>(?:</script>)?',
    _inline_script,
    html,
)

# Inline all CSS assets referenced in the HTML.
def _inline_style(match: re.Match) -> str:
    href = match.group(1)                      # e.g. "./assets/index-abc.css"
    rel = href.lstrip("./")
    css_path = dist_path / rel
    if css_path.exists():
        content = css_path.read_text(encoding="utf-8")
        return f'<style>{content}</style>'
    return match.group(0)

html = re.sub(
    r'<link\b[^>]*\brel="stylesheet"\b[^>]*\bhref="(\./[^"]+\.css)"[^>]*/?>',
    _inline_style,
    html,
)

# Render the fully self-contained app inside Streamlit's component iframe
components.html(html, height=920, scrolling=True)
