import streamlit as st
import streamlit.components.v1 as components
import pathlib

st.set_page_config(
    page_title="Cosmos 3 AI Image Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit's default chrome for a full-page experience
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
gemini_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
hf_token   = st.secrets.get("HF_TOKEN", "") if hasattr(st, "secrets") else ""

# Load the built React app index.html
dist_path = pathlib.Path(__file__).parent / "dist" / "index.html"

if not dist_path.exists():
    st.error(
        "⚠️ **Build files not found!**\n\n"
        "Please run `npm run build` inside the `cosmos-studio/` directory first, "
        "then commit the generated `dist/` folder to your repository.",
        icon="🚨"
    )
    st.code("cd cosmos-studio\nnpm run build", language="bash")
    st.stop()

html_content = dist_path.read_text(encoding="utf-8")

# Inject API keys as window-scoped globals BEFORE </head>
# Keys are served server-side and never stored in source code
injection_script = f"""
<script>
  // Injected by Streamlit backend — do not edit manually
  window.__GEMINI_API_KEY__ = "{gemini_key}";
  window.__HF_TOKEN__ = "{hf_token}";
</script>
"""

html_content = html_content.replace("</head>", injection_script + "</head>", 1)

# Fix asset paths: Vite generates absolute paths like /assets/... but
# when served inside Streamlit's iframe, we need relative paths.
# The built index.html uses relative paths by default with base: "./" in vite.config.ts
# so this is typically not needed — but we add a safeguard here.
html_content = html_content.replace('src="/', 'src="./')
html_content = html_content.replace('href="/', 'href="./')

# Serve the full React app inside a Streamlit component iframe
# Height is set large; the inner React app is min-h-screen so it fills the iframe
components.html(
    html_content,
    height=1080,
    scrolling=True,
)
