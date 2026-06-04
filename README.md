# 🎨 Cosmos 3 AI Image Studio

A premium AI image generation web application powered by **NVIDIA Cosmos 3 Super (64B)** and **Google Imagen 4.0**, built with React + Vite + Tailwind CSS and deployed via Streamlit.

![Cosmos 3 AI Studio](https://images.unsplash.com/photo-1616401784845-180882ba9ba8?auto=format&fit=crop&w=1024&q=80)

## ✨ Features

- 🤖 **Dual AI Engines**: NVIDIA Cosmos 3 Super via Hugging Face API + Google Imagen 4.0
- ✨ **AI Prompt Optimizer**: Gemini 2.5 Flash expands simple ideas into detailed physics-rich prompts
- 🎛️ **Advanced Controls**: CFG guidance scale, inference steps, aspect ratio, seed control
- 📚 **Example Library**: 4 curated prompts showcasing Cosmos 3's physical realism strengths
- 🖼️ **History Gallery**: Browse and re-select past generations within session
- 💻 **Code Export**: Live Python & cURL code generation from current settings
- 🏗️ **Architecture Diagram**: Educational system flow diagram for students

## 🚀 Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.8+
- pip

### 1. Install & Build React App

```bash
npm install
npm run build
```

### 2. Set Up Python Environment

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Edit `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-google-gemini-api-key"
HF_TOKEN = "hf_your_hugging_face_read_token"
```

**Get your keys:**
- **Gemini API Key**: https://aistudio.google.com/app/apikey
- **Hugging Face Token**: https://huggingface.co/settings/tokens (Read permission)

### 4. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 🌐 Deploy to Streamlit Community Cloud

1. **Push this repository to GitHub** (make sure `dist/` is committed):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Cosmos 3 AI Image Studio"
   git remote add origin https://github.com/YOUR_USERNAME/cosmos-studio.git
   git push -u origin main
   ```

2. **Go to** https://share.streamlit.io and click **"New app"**

3. **Configure the app:**
   - Repository: `YOUR_USERNAME/cosmos-studio`
   - Branch: `main`
   - Main file path: `app.py`

4. **Set Secrets** in the Streamlit Cloud dashboard (App Settings → Secrets):
   ```toml
   GEMINI_API_KEY = "your-google-gemini-api-key"
   HF_TOKEN = "hf_your_hugging_face_read_token"
   ```

5. Click **Deploy** 🎉

---

## 🏗️ Architecture

```
User Browser
    ↓
Streamlit (app.py)
    ├── Reads secrets from Streamlit Cloud secrets
    ├── Loads dist/index.html
    ├── Injects window.__GEMINI_API_KEY__ + window.__HF_TOKEN__
    └── Serves via st.components.v1.html()
         ↓
    React App (Vite build)
         ├── Reads injected API keys from window globals
         ├── Gemini 2.5 Flash → Prompt optimization
         ├── HF Serverless API → nvidia/Cosmos3-Super-Text2Image
         └── Google Imagen 4.0 → image generation
```

## 📁 Project Structure

```
cosmos-studio/
├── src/
│   ├── App.tsx          # Main React component
│   ├── main.tsx         # React entry point
│   └── index.css        # Tailwind CSS directives
├── dist/                # Built React app (committed for Streamlit)
├── app.py               # Streamlit wrapper with key injection
├── requirements.txt     # Python dependencies
├── vite.config.ts       # Vite config (base: './')
├── tailwind.config.js   # Tailwind content paths
├── .streamlit/
│   ├── config.toml      # Streamlit server config
│   └── secrets.toml     # Local dev secrets (gitignored)
└── .gitignore
```

## 🔒 Security Notes

- API keys are **never stored in source code**
- Keys are injected **server-side** by Python into the HTML at request time
- The `.streamlit/secrets.toml` file is **gitignored**
- Users can also input their own HF Token in the UI (stored in browser localStorage only)

## 📄 License

MIT — Educational use. Built as a student innovation project exploring AI image generation.
