import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Image as ImageIcon, 
  Settings, 
  Sliders, 
  Play, 
  RotateCcw, 
  Download, 
  Copy, 
  HelpCircle, 
  Check, 
  Info, 
  AlertTriangle, 
  Key, 
  ArrowRight, 
  Code, 
  History, 
  Cpu, 
  Layers,
  ExternalLink,
  BookOpen,
  Terminal,
  Grid
} from 'lucide-react';

// API keys injected by Streamlit backend at runtime (window globals)
declare global {
  interface Window {
    __GEMINI_API_KEY__?: string;
    __HF_TOKEN__?: string;
  }
}

const apiKey = window.__GEMINI_API_KEY__ || '';

export default function App() {
  // 核心狀態管理
  const [activeTab, setActiveTab] = useState('generator'); // 'generator', 'architecture', 'code'
  const [engine, setEngine] = useState('cosmos3'); // 'cosmos3' (HF), 'gemini' (Imagen 4.0)
  const [hfToken, setHfToken] = useState(() => {
    // Pre-fill from Streamlit-injected token or localStorage
    return window.__HF_TOKEN__ || localStorage.getItem('cosmos_hf_token') || '';
  });
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('blurry, low quality, distorted, bad physics, text, watermark');
  const [_expandedPrompt, setExpandedPrompt] = useState('');
  const [isExpanding, setIsExpanding] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // 生成設定參數
  const [aspectRatio, setAspectRatio] = useState('1:1'); // '1:1', '16:9', '9:16'
  const [guidanceScale, setGuidanceScale] = useState(7.0);
  const [inferenceSteps, setInferenceSteps] = useState(25);
  const [seed, setSeed] = useState(-1);

  // 歷史與展示紀錄
  const [historyList, setHistoryList] = useState<any[]>(() => {
    const saved = localStorage.getItem('cosmos_history');
    return saved ? JSON.parse(saved) : [
      {
        id: 'sample-1',
        prompt: 'An advanced industrial robotic arm assembling an electric vehicle battery in a pristine futuristic Gigafactory. Intense physical realism, detailed pneumatic tubes, metallic reflections, glowing status LEDs, precise cinematic lighting.',
        engine: 'cosmos3 (Demo)',
        aspectRatio: '16:9',
        imageUrl: 'https://images.unsplash.com/photo-1616401784845-180882ba9ba8?auto=format&fit=crop&w=1024&q=80',
        timestamp: new Date().toLocaleTimeString(),
        steps: 25,
        cfg: 7.0
      },
      {
        id: 'sample-2',
        prompt: 'A breathtaking wide-angle shot of Milford Sound, New Zealand. Mirror-like water reflecting massive fjords and waterfalls, dramatic mist rolling between the peaks, golden hour sunlight piercing through the storm clouds, hyper-detailed moss.',
        engine: 'cosmos3 (Demo)',
        aspectRatio: '16:9',
        imageUrl: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1024&q=80',
        timestamp: new Date().toLocaleTimeString(),
        steps: 25,
        cfg: 7.0
      }
    ];
  });
  const [selectedImage, setSelectedImage] = useState<any>(historyList[0] || null);

  // 儲存 Token 到 LocalStorage
  useEffect(() => {
    localStorage.setItem('cosmos_hf_token', hfToken);
  }, [hfToken]);

  // 儲存歷史紀錄
  useEffect(() => {
    localStorage.setItem('cosmos_history', JSON.stringify(historyList));
  }, [historyList]);

  // Toast 通知管理
  const triggerToast = (msg: string, type = 'success') => {
    if (type === 'success') {
      setSuccessMsg(msg);
      setTimeout(() => setSuccessMsg(null), 3000);
    } else {
      setErrorMsg(msg);
      setTimeout(() => setErrorMsg(null), 5000);
    }
  };

  // 指數退避 (Exponential Backoff) 網路重試機制
  const fetchWithRetry = async (url: string, options: RequestInit, maxRetries = 5): Promise<Response> => {
    let delay = 1000;
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, options);
        if (response.status === 429 || response.status >= 500) {
          if (i === maxRetries - 1) throw new Error(`伺服器忙碌中或發生錯誤 (HTTP ${response.status})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          delay *= 2;
          continue;
        }
        return response;
      } catch (error) {
        if (i === maxRetries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2;
      }
    }
    throw new Error('Max retries exceeded');
  };

  // 1. 呼叫 Gemini 2.5 Flash 進行 Prompt 擴寫與優化
  const handleOptimizePrompt = async () => {
    if (!prompt.trim()) {
      triggerToast('請先輸入基本的提示詞構想！', 'error');
      return;
    }

    setIsExpanding(true);
    setErrorMsg(null);

    const systemPrompt = `你是一個專業的 AI 繪圖 Prompt 提示詞優化專家。
請將用戶輸入的簡單想法或提示詞，擴寫為適合 NVIDIA Cosmos 3 超高畫質物理圖像生成模型使用的詳細英文 Prompt。
Cosmos 3 是一個物理真實性極高、世界模擬能力極強的模型，特別擅長細節、材質、物理光學、空間感。
請輸出一個高水準的結構化英文 Prompt，包含：主體(Subject)、物理細節(Physical details)、光影(Lighting)、材質與質地(Textures & Materials)、相機透視(Camera perspective)。
注意：請直接輸出最終的英文 Prompt 內容即可，千萬不要包含任何額外的解釋、引言、Markdown 標籤或符號。`;

    const userQuery = `請優化以下提示詞：\n"${prompt}"`;

    try {
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
      const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] }
      };

      const response = await fetchWithRetry(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('無法連接到 Gemini 擴寫服務。');

      const data = await response.json();
      const enhancedText = data.candidates?.[0]?.content?.parts?.[0]?.text;
      
      if (enhancedText) {
        setExpandedPrompt(enhancedText.trim());
        setPrompt(enhancedText.trim());
        triggerToast('✨ Prompt 優化成功！已填入主輸入框');
      } else {
        throw new Error('無法解析優化後的提示詞。');
      }
    } catch (err: any) {
      triggerToast(`擴寫失敗: ${err.message}，已保留原提示詞。`, 'error');
    } finally {
      setIsExpanding(false);
    }
  };

  // 2. 生成圖像主流程
  const handleGenerateImage = async () => {
    if (!prompt.trim()) {
      triggerToast('請輸入提示詞！', 'error');
      return;
    }

    setIsGenerating(true);
    setErrorMsg(null);
    setLoadingStep('正在初始化生成引擎...');

    try {
      if (engine === 'cosmos3') {
        if (!hfToken.trim()) {
          throw new Error('請在右側「Hugging Face 金鑰設定」中填入您的 HF API Token，或切換至「Gemini 免費體驗引擎」！');
        }

        setLoadingStep('正在連結 Hugging Face 推理伺服器...');
        
        let width = 1024, height = 1024;
        if (aspectRatio === '16:9') { width = 1024; height = 576; }
        else if (aspectRatio === '9:16') { width = 576; height = 1024; }

        const hfPayload = {
          inputs: prompt,
          parameters: {
            negative_prompt: negativePrompt,
            guidance_scale: Number(guidanceScale),
            num_inference_steps: Number(inferenceSteps),
            width: width,
            height: height,
            seed: seed === -1 ? Math.floor(Math.random() * 100000) : Number(seed)
          }
        };

        setLoadingStep('NVIDIA Cosmos 3 正在進行物理世界矩陣運算 (約需 10-30 秒)...');
        
        const response = await fetchWithRetry(
          "https://api-inference.huggingface.co/models/nvidia/Cosmos3-Super-Text2Image",
          {
            headers: { 
              "Authorization": `Bearer ${hfToken.trim()}`,
              "Content-Type": "application/json"
            },
            method: "POST",
            body: JSON.stringify(hfPayload),
          }
        );

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error((errData as any).error || `Hugging Face 回傳錯誤: ${response.statusText}。請確認 Token 是否有效，或模型是否正在加載。`);
        }

        setLoadingStep('正在接收高清圖像數據編碼...');
        const imageBlob = await response.blob();
        const localImageUrl = URL.createObjectURL(imageBlob);

        const newRecord = {
          id: `gen-${Date.now()}`,
          prompt: prompt,
          engine: 'nvidia/Cosmos3-Super-Text2Image',
          aspectRatio: aspectRatio,
          imageUrl: localImageUrl,
          timestamp: new Date().toLocaleTimeString(),
          steps: inferenceSteps,
          cfg: guidanceScale
        };

        setHistoryList(prev => [newRecord, ...prev]);
        setSelectedImage(newRecord);
        triggerToast('🎨 Cosmos 3 圖像生成成功！');

      } else {
        setLoadingStep('正在連結 Google Imagen 4.0 圖像生成伺服器...');
        
        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${apiKey}`;
        const imagenPayload = {
          instances: { prompt: prompt },
          parameters: { sampleCount: 1 }
        };

        const response = await fetchWithRetry(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(imagenPayload)
        });

        if (!response.ok) {
          throw new Error(`Google Imagen API 回傳錯誤 (${response.status})。`);
        }

        setLoadingStep('正在轉換並解碼 Base64 圖像數據...');
        const result = await response.json();
        const base64Data = result.predictions?.[0]?.bytesBase64Encoded;

        if (!base64Data) {
          throw new Error('未接收到有效的圖像編碼數據。');
        }

        const localImageUrl = `data:image/png;base64,${base64Data}`;

        const newRecord = {
          id: `gen-${Date.now()}`,
          prompt: prompt,
          engine: 'Gemini Imagen 4.0',
          aspectRatio: '1:1',
          imageUrl: localImageUrl,
          timestamp: new Date().toLocaleTimeString(),
          steps: 'Auto',
          cfg: 'Auto'
        };

        setHistoryList(prev => [newRecord, ...prev]);
        setSelectedImage(newRecord);
        triggerToast('🎨 Gemini Imagen 圖像生成成功！');
      }

    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message);
      triggerToast(err.message, 'error');
    } finally {
      setIsGenerating(false);
      setLoadingStep('');
    }
  };

  const handleApplyExample = (text: string) => {
    setPrompt(text);
    triggerToast('已套用範例提示詞！');
  };

  const handleCopyText = (text: string, label = '文字') => {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      triggerToast(`📋 已複製${label}到剪貼簿！`);
    } catch (err) {
      triggerToast('複製失敗，請手動複製。', 'error');
    }
    document.body.removeChild(textArea);
  };

  const handleResetSettings = () => {
    setPrompt('');
    setNegativePrompt('blurry, low quality, distorted, bad physics, text, watermark');
    setAspectRatio('1:1');
    setGuidanceScale(7.0);
    setInferenceSteps(25);
    setSeed(-1);
    triggerToast('已重設所有生成參數。');
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-[#76b900] selection:text-black">
      
      {/* 頂部導覽列 Header */}
      <header className="border-b border-slate-800 bg-[#0c1220]/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo 與標題 */}
          <div className="flex items-center space-x-3">
            <div className="bg-[#76b900] p-2 rounded-xl text-black shadow-[0_0_15px_rgba(118,185,0,0.4)] flex items-center justify-center">
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-white">Cosmos 3 AI</h1>
                <span className="bg-[#76b900]/10 text-[#76b900] text-[10px] font-semibold px-2 py-0.5 rounded border border-[#76b900]/20">
                  NVIDIA Model Base
                </span>
              </div>
              <p className="text-xs text-slate-400">學生創新專題：高真物理影像生成學堂</p>
            </div>
          </div>

          {/* 導覽頁籤 */}
          <nav className="flex items-center space-x-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
            <button 
              onClick={() => setActiveTab('generator')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'generator' 
                  ? 'bg-slate-800 text-[#76b900] shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              <span>創意繪圖板</span>
            </button>
            <button 
              onClick={() => setActiveTab('architecture')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'architecture' 
                  ? 'bg-slate-800 text-[#76b900] shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>系統架構圖</span>
            </button>
            <button 
              onClick={() => setActiveTab('code')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'code' 
                  ? 'bg-slate-800 text-[#76b900] shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>程式碼整合</span>
            </button>
          </nav>

          {/* 狀態指示燈 */}
          <div className="flex items-center space-x-3 text-xs">
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${hfToken ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-amber-500 shadow-[0_0_8px_#f59e0b]'}`}></span>
              <span className="text-slate-300">HF Token: {hfToken ? '已配置' : '未設定'}</span>
            </div>
          </div>

        </div>
      </header>

      {/* 警告/訊息提示 Toast 區塊 */}
      {errorMsg && (
        <div className="bg-rose-950/80 border-b border-rose-800 text-rose-200 px-4 py-3 text-xs flex items-center justify-center space-x-2 transition-all">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span><strong>錯誤提示：</strong> {errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="bg-emerald-950/80 border-b border-emerald-800 text-emerald-200 px-4 py-3 text-xs flex items-center justify-center space-x-2 transition-all">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* 主體內容區域 */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 flex flex-col gap-6">

        {activeTab === 'generator' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* 左側：核心控制面版 (佔 5 格) */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              
              {/* 引擎切換 & Token 設置面板 */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                    <Sliders className="w-4 h-4 text-[#76b900]" />
                    <span>1. 選擇生成模型與權杖</span>
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">STEP 01</span>
                </div>

                {/* 引擎切換按鈕 */}
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800 mb-4">
                  <button
                    onClick={() => setEngine('cosmos3')}
                    className={`py-2 px-3 rounded-lg text-xs font-medium transition-all flex flex-col items-center justify-center ${
                      engine === 'cosmos3'
                        ? 'bg-[#76b900] text-black font-bold shadow-md'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <span>Cosmos 3 Super (64B)</span>
                    <span className="text-[9px] opacity-80 mt-0.5">Hugging Face 雲端運算</span>
                  </button>
                  <button
                    onClick={() => setEngine('gemini')}
                    className={`py-2 px-3 rounded-lg text-xs font-medium transition-all flex flex-col items-center justify-center ${
                      engine === 'gemini'
                        ? 'bg-emerald-600 text-white font-bold shadow-md'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <span>Imagen 4.0</span>
                    <span className="text-[9px] opacity-80 mt-0.5">Google 內建免 Token 體驗</span>
                  </button>
                </div>

                {/* HF Token 輸入框 */}
                {engine === 'cosmos3' ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs text-slate-300 font-medium flex items-center space-x-1">
                        <Key className="w-3.5 h-3.5 text-amber-400" />
                        <span>Hugging Face Access Token (Read權限)</span>
                      </label>
                      <a 
                        href="https://huggingface.co/settings/tokens" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-[10px] text-slate-400 hover:text-[#76b900] flex items-center space-x-0.5"
                      >
                        <span>去申請</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>
                    <div className="relative">
                      <input
                        type="password"
                        placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                        value={hfToken}
                        onChange={(e) => setHfToken(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#76b900] transition-colors text-slate-200 pr-10"
                      />
                      {hfToken ? (
                        <Check className="w-4 h-4 text-emerald-400 absolute right-3 top-2.5" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500 absolute right-3 top-2.5" />
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500">
                      提示：您的 Token 會安全儲存在您的瀏覽器中，不會傳送到外部任何第三方伺服器。
                    </p>
                  </div>
                ) : (
                  <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-xl p-3 text-xs text-emerald-300/90 flex items-start space-x-2">
                    <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold">Gemini 內建沙盒引擎運作中</p>
                      <p className="text-[11px] text-emerald-400/80 mt-0.5">
                        本應用已安全對接 Imagen 4.0 圖像生成接口，適合直接在 Canvas 中演示。完成作業部署前，請記得配置 Hugging Face Token 以體驗 Cosmos 3 的強大威力。
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* 提示詞輸入與智慧擴寫面板 */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm flex-1 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-[#76b900]" />
                    <span>2. 輸入繪圖提示詞 (Prompts)</span>
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">STEP 02</span>
                </div>

                <div className="relative flex-1 min-h-[120px] flex flex-col">
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="例如：An advanced industrial robotic arm assembling an electric vehicle... (建議以詳細英文輸入，或點擊下方擴寫按鈕)"
                    className="w-full flex-1 bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-[#76b900] transition-colors resize-none leading-relaxed min-h-[120px]"
                  />
                  
                  {/* AI 提示詞優化按鈕 */}
                  <div className="absolute right-2.5 bottom-2.5 flex items-center space-x-2">
                    <button
                      type="button"
                      disabled={isExpanding || !prompt.trim()}
                      onClick={handleOptimizePrompt}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-sm ${
                        !prompt.trim()
                          ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                          : isExpanding
                          ? 'bg-slate-800 text-[#76b900] animate-pulse'
                          : 'bg-[#76b900] hover:bg-[#87cf03] text-black font-bold'
                      }`}
                      title="使用 Gemini 智慧大語言模型將您的簡單詞彙，擴寫為精準的 Cosmos 3 物理架構提示詞"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{isExpanding ? '擴寫中...' : '✨ AI 擴寫 (Gemini 優化)'}</span>
                    </button>
                  </div>
                </div>

                {/* 負向提示詞 */}
                {engine === 'cosmos3' && (
                  <div className="space-y-1.5">
                    <span className="text-xs text-slate-400 block font-medium">不希望出現的特徵 (Negative Prompt)：</span>
                    <input
                      type="text"
                      value={negativePrompt}
                      onChange={(e) => setNegativePrompt(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-[#76b900]"
                    />
                  </div>
                )}

                {/* 進階繪圖參數控制 */}
                {engine === 'cosmos3' && (
                  <div className="border-t border-slate-800/80 pt-4 space-y-4">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-semibold text-slate-300 flex items-center space-x-1">
                        <Settings className="w-3.5 h-3.5 text-[#76b900]" />
                        <span>3. 進階參數微調</span>
                      </span>
                      <button 
                        onClick={handleResetSettings}
                        className="text-[10px] text-slate-500 hover:text-white flex items-center space-x-1"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>重設參數</span>
                      </button>
                    </div>

                    {/* 寬高比例 Aspect Ratio */}
                    <div className="space-y-1.5">
                      <span className="text-xs text-slate-400 block">畫面比例 (Aspect Ratio)</span>
                      <div className="grid grid-cols-3 gap-2">
                        {['1:1', '16:9', '9:16'].map((ratio) => (
                          <button
                            key={ratio}
                            onClick={() => setAspectRatio(ratio)}
                            className={`py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                              aspectRatio === ratio
                                ? 'bg-slate-800 border-[#76b900] text-[#76b900]'
                                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                            }`}
                          >
                            {ratio === '1:1' ? '1:1 正方形' : ratio === '16:9' ? '16:9 寬螢幕' : '9:16 肖像畫'}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* CFG Guidance & Inference Steps */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">提示詞相關度 (CFG)</span>
                          <span className="text-[#76b900] font-mono">{guidanceScale}</span>
                        </div>
                        <input
                          type="range"
                          min="1"
                          max="20"
                          step="0.5"
                          value={guidanceScale}
                          onChange={(e) => setGuidanceScale(parseFloat(e.target.value))}
                          className="w-full accent-[#76b900] bg-slate-950"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">去噪步數 (Steps)</span>
                          <span className="text-[#76b900] font-mono">{inferenceSteps}</span>
                        </div>
                        <input
                          type="range"
                          min="10"
                          max="50"
                          step="1"
                          value={inferenceSteps}
                          onChange={(e) => setInferenceSteps(parseInt(e.target.value))}
                          className="w-full accent-[#76b900] bg-slate-950"
                        />
                      </div>
                    </div>

                    {/* 隨機種子 Seed */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">隨機種子 (Seed, -1 為隨機)</span>
                        <span className="text-slate-500 font-mono">{seed === -1 ? 'Random' : seed}</span>
                      </div>
                      <input
                        type="number"
                        value={seed}
                        onChange={(e) => setSeed(parseInt(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-[#76b900]"
                        placeholder="-1"
                      />
                    </div>
                  </div>
                )}

                {/* 執行核心生成按鈕 */}
                <button
                  onClick={handleGenerateImage}
                  disabled={isGenerating}
                  className={`w-full py-3.5 rounded-xl font-bold text-sm tracking-wide transition-all shadow-[0_4px_20px_rgba(118,185,0,0.2)] flex items-center justify-center space-x-2 ${
                    isGenerating
                      ? 'bg-slate-800 text-slate-500 cursor-wait'
                      : 'bg-[#76b900] hover:bg-[#87cf03] text-black'
                  }`}
                >
                  {isGenerating ? (
                    <>
                      <div className="w-5 h-5 border-2 border-slate-500 border-t-[#76b900] rounded-full animate-spin"></div>
                      <span>正在繪製影像，請稍候...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>
                        開始生成 {engine === 'cosmos3' ? 'Cosmos 3 Super 影像' : 'Imagen 4.0 影像'}
                      </span>
                    </>
                  )}
                </button>

              </div>

            </div>

            {/* 右側：圖像生成畫布 & 生成歷史展示 (佔 7 格) */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              
              {/* 圖像主工作區 */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm flex flex-col justify-between min-h-[460px]">
                
                {/* 頂部控制面板 */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#76b900] animate-ping"></span>
                    <span>AI 核心畫布區</span>
                  </span>
                  
                  {selectedImage && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleCopyText(selectedImage.prompt, 'Prompt 提示詞')}
                        className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors"
                        title="複製提示詞"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <a
                        href={selectedImage.imageUrl}
                        download={`cosmos3-${selectedImage.id}.jpg`}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-[#76b900] transition-colors flex items-center space-x-1"
                        title="下載高畫質大圖"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold">下載大圖</span>
                      </a>
                    </div>
                  )}
                </div>

                {/* 畫布顯示核心 */}
                <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 rounded-xl border border-slate-800 overflow-hidden relative min-h-[300px] p-4">
                  {isGenerating ? (
                    <div className="flex flex-col items-center text-center max-w-sm px-4">
                      <div className="relative mb-6">
                        <div className="w-20 h-20 rounded-full border-4 border-slate-800 border-t-[#76b900] animate-spin"></div>
                        <Cpu className="w-8 h-8 text-[#76b900] absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-bounce" />
                      </div>
                      <h4 className="text-white text-sm font-semibold mb-2">
                        正在調度 GPU 算力集群
                      </h4>
                      <p className="text-xs text-[#76b900] font-mono bg-[#76b900]/10 border border-[#76b900]/20 px-3 py-1 rounded-full animate-pulse">
                        {loadingStep}
                      </p>
                      <p className="text-[10px] text-slate-500 mt-4 leading-relaxed">
                        NVIDIA Cosmos 3 (64 Billion Parameters) 使用了創新的 3D 複合注意力機制與 Transformer 架構，首次加載可能需要稍長的時間。
                      </p>
                    </div>
                  ) : selectedImage ? (
                    <div className="w-full h-full flex flex-col items-center justify-center">
                      <div className="max-h-[380px] rounded-lg overflow-hidden border border-slate-800/80 shadow-2xl relative group">
                        <img
                          src={selectedImage.imageUrl}
                          alt="AI Generated"
                          className="object-contain max-h-[380px] w-auto transition-transform duration-300 group-hover:scale-105"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.onerror = null;
                            target.src = 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=800&q=80';
                            triggerToast('大圖載入失敗，已加載預設示意圖', 'error');
                          }}
                        />
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          <p className="text-[10px] text-[#76b900] font-bold tracking-wider">
                            MODEL: {selectedImage.engine}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center max-w-sm px-6 py-12">
                      <div className="w-16 h-16 bg-slate-900 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-800 text-slate-500">
                        <ImageIcon className="w-8 h-8" />
                      </div>
                      <h4 className="text-slate-300 text-sm font-semibold mb-1">準備就緒，等候指令</h4>
                      <p className="text-xs text-slate-500 leading-relaxed mb-4">
                        請在左側輸入提示詞並點擊「開始生成」，或者直接套用下方的學術示範提示詞快速體驗！
                      </p>
                    </div>
                  )}
                </div>

                {/* 底部生成細節 */}
                {selectedImage && !isGenerating && (
                  <div className="mt-4 bg-slate-950 rounded-xl p-3 border border-slate-800 text-xs">
                    <p className="text-slate-300 font-medium mb-1.5 leading-relaxed">
                      💡 <span className="text-[#76b900] font-semibold">生成 Prompt:</span> {selectedImage.prompt}
                    </p>
                    <div className="flex flex-wrap gap-x-4 gap-y-2 mt-2 pt-2 border-t border-slate-900 text-slate-400 font-mono text-[11px]">
                      <span>引擎: <span className="text-slate-200">{selectedImage.engine}</span></span>
                      <span>去噪步數: <span className="text-slate-200">{selectedImage.steps}</span></span>
                      <span>引導系數: <span className="text-slate-200">{selectedImage.cfg}</span></span>
                      <span>比例: <span className="text-slate-200">{selectedImage.aspectRatio}</span></span>
                      <span className="ml-auto text-slate-500">{selectedImage.timestamp}</span>
                    </div>
                  </div>
                )}

              </div>

              {/* 快速示範與範例 Prompt */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
                <h3 className="text-sm font-semibold text-white flex items-center space-x-2 mb-3">
                  <BookOpen className="w-4 h-4 text-[#76b900]" />
                  <span>教學範例庫 (點擊直接套用)</span>
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    {
                      title: "🤖 未來物理工廠 (Cosmos擅長)",
                      desc: "An advanced industrial robotic arm assembling an electric vehicle battery in a pristine futuristic Gigafactory. Intense physical realism, detailed pneumatic tubes, metallic reflections.",
                    },
                    {
                      title: "🌧️ 台北賽博朋克夜色 (光影反射)",
                      desc: "A cinematic hyper-realistic shot of Taipei City in the year 2099. Cyberpunk skyscrapers with giant holograms, wet street reflecting multi-colored neon signs in Traditional Chinese.",
                    },
                    {
                      title: "🌊 紐西蘭魔戒峽灣 (大自然細節)",
                      desc: "A breathtaking wide-angle shot of Milford Sound, New Zealand. Mirror-like water reflecting massive fjords and waterfalls, golden hour sunlight piercing through storm clouds.",
                    },
                    {
                      title: "🔮 桌上懸浮星系 (折射玻璃)",
                      desc: "A floating glass sphere holding a miniature solar system inside. The glass sphere is sitting on a dark volcanic beach sand, reflecting ocean waves. Macro shot, highly detailed.",
                    }
                  ].map((item, index) => (
                    <button
                      key={index}
                      onClick={() => handleApplyExample(item.desc)}
                      className="bg-slate-950/80 hover:bg-slate-900 text-left p-3 rounded-xl border border-slate-800 hover:border-[#76b900]/50 transition-all flex flex-col group"
                    >
                      <span className="text-xs font-semibold text-slate-200 group-hover:text-[#76b900] transition-colors mb-1">
                        {item.title}
                      </span>
                      <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">
                        {item.desc}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {/* 生成歷史畫廊 */}
              {historyList.length > 0 && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                      <History className="w-4 h-4 text-[#76b900]" />
                      <span>本次繪圖歷程紀錄 ({historyList.length})</span>
                    </h3>
                    <button
                      onClick={() => {
                        if(confirm('確認清空歷史紀錄？')) {
                          setHistoryList([]);
                          setSelectedImage(null);
                        }
                      }}
                      className="text-[10px] text-rose-400 hover:text-rose-300 font-medium"
                    >
                      清空歷史
                    </button>
                  </div>

                  <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                    {historyList.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => setSelectedImage(item)}
                        className={`aspect-square rounded-lg overflow-hidden border-2 relative transition-all ${
                          selectedImage?.id === item.id 
                            ? 'border-[#76b900] scale-95 shadow-[0_0_8px_rgba(118,185,0,0.5)]' 
                            : 'border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <img 
                          src={item.imageUrl} 
                          alt="History thumb" 
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/30 hover:bg-transparent transition-colors"></div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

            </div>

          </div>
        )}

        {/* 頁籤 2：系統與 API 架構分析 */}
        {activeTab === 'architecture' && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm space-y-8">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <Layers className="w-5 h-5 text-[#76b900]" />
                <span>NVIDIA Cosmos 3 Web App 系統運作架構</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                幫助學生理解前後端、Hugging Face 雲端算力與 Gemini 智慧擴寫大語言模型之間的「模型鏈 (Model Chaining)」與傳輸機制。
              </p>
            </div>

            {/* 架構流程圖 */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center bg-slate-950 p-6 rounded-xl border border-slate-800">
              
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center flex flex-col items-center">
                <div className="w-10 h-10 bg-[#76b900]/10 text-[#76b900] rounded-full flex items-center justify-center mb-2">
                  <Sliders className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-bold text-white mb-1">1. 前端 React UI</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  輸入中文或英文創意，設定 CFG、去噪步數與長寬比。
                </p>
              </div>

              <div className="hidden md:flex justify-center text-slate-600">
                <ArrowRight className="w-6 h-6" />
              </div>

              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center flex flex-col items-center relative">
                <div className="absolute -top-2.5 bg-indigo-500 text-white text-[9px] px-1.5 py-0.5 rounded-full font-bold">
                  選用功能
                </div>
                <div className="w-10 h-10 bg-indigo-500/10 text-indigo-400 rounded-full flex items-center justify-center mb-2">
                  <Sparkles className="w-5 h-5 animate-pulse" />
                </div>
                <h4 className="text-xs font-bold text-white mb-1">2. Gemini 提示大師</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  大模型自動將直覺字彙擴寫為包含光影、物理材質的 3D 物理提示詞。
                </p>
              </div>

              <div className="hidden md:flex justify-center text-slate-600">
                <ArrowRight className="w-6 h-6" />
              </div>

              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center flex flex-col items-center">
                <div className="w-10 h-10 bg-amber-500/10 text-amber-400 rounded-full flex items-center justify-center mb-2">
                  <Cpu className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-bold text-white mb-1">3. HF Serverless API</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  攜帶 Bearer Token 傳送 POST 請求至 nvidia/Cosmos3 推理端點。
                </p>
              </div>

              <div className="hidden md:flex justify-center text-slate-600 md:col-start-2">
                <ArrowRight className="w-6 h-6" />
              </div>

              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center flex flex-col items-center">
                <div className="w-10 h-10 bg-rose-500/10 text-rose-400 rounded-full flex items-center justify-center mb-2">
                  <Grid className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-bold text-white mb-1">4. Cosmos 3 (64B)</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  Mixture-of-Transformers 模型在多張 H100 進行高效能物理去噪。
                </p>
              </div>

              <div className="hidden md:flex justify-center text-slate-600">
                <ArrowRight className="w-6 h-6" />
              </div>

              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center flex flex-col items-center">
                <div className="w-10 h-10 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mb-2">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-bold text-white mb-1">5. 圖像還原</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  將回傳的 Blob 二進制數據還原，轉化成網頁 Image 渲染，完成流程。
                </p>
              </div>

            </div>

            {/* 模型技術特性介紹 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                <h4 className="text-sm font-bold text-[#76b900] flex items-center space-x-1.5">
                  <Cpu className="w-4 h-4" />
                  <span>NVIDIA Cosmos 3 Super 旗艦優勢</span>
                </h4>
                <ul className="text-xs text-slate-300 space-y-2 list-disc pl-4 leading-relaxed">
                  <li><strong>物理世界大模型：</strong> 不僅是靜態畫素，Cosmos 3 還兼備了物理世界模擬器、行動推理與高感光物理重現能力。</li>
                  <li><strong>640 億巨大參數量：</strong> 由 32B Autoregressive 推理塔與 32B Diffusion 生成塔組成的「雙塔式混合架構」。</li>
                  <li><strong>3D 旋轉位置編碼：</strong> 採用 mRoPE 技術，實現視覺、音訊、文字等多模態空間與時間軸的無縫貼合。</li>
                  <li><strong>高保真度與物理光學：</strong> 在玻璃折射、金屬材質、流體重力等物理常規基準上，全面領先市面上同級開源模型。</li>
                </ul>
              </div>

              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                <h4 className="text-sm font-bold text-[#76b900] flex items-center space-x-1.5">
                  <HelpCircle className="w-4 h-4" />
                  <span>學生實驗專題思考與討論</span>
                </h4>
                <div className="text-xs text-slate-300 space-y-3 leading-relaxed">
                  <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                    <span className="font-semibold text-amber-400">思考一：為什麼 Cosmos 3 本地部署極為困難？</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      因其高達 64B 的參數量，完整本地推演需要超過 128GB VRAM。這凸顯了本專題引導使用「Hugging Face API 雲端推理」在輕量網頁應用的實用性。
                    </p>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                    <span className="font-semibold text-amber-400">思考二：何謂 AI 提示詞擴寫 (Prompt Upsampling)？</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Cosmos 3 是物理導向的模型，當你輸入簡單的主題時，LLM 能夠預測物理細節、燈光、焦距等輔助資訊，從而產生具備物理真實感（Physical Realism）的高水準畫作。
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* 頁籤 3：多語言整合程式碼 */}
        {activeTab === 'code' && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <Code className="w-5 h-5 text-[#76b900]" />
                <span>後端與命令列自動化整合代碼 (API Integration)</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                此功能會根據您在「創意繪圖板」中配置的 Prompt 及設定，自動即時轉譯成 Python 腳本或 cURL 命令，學生可以直接複製到 Jupyter Notebook 或 Linux Terminal 中進行後端程式化批量生成。
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Python 整合腳本 */}
              <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#76b900] flex items-center space-x-1.5">
                    <Terminal className="w-3.5 h-3.5" />
                    <span>Python requests 腳本</span>
                  </span>
                  <button
                    onClick={() => handleCopyText(
`import requests

# 1. 配置 API 端點與 Access Token
API_URL = "https://api-inference.huggingface.co/models/nvidia/Cosmos3-Super-Text2Image"
headers = {"Authorization": "Bearer ${hfToken || 'YOUR_HF_TOKEN_HERE'}"}

def query_cosmos(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"API Error: {response.text}")
    return response.content

payload = {
    "inputs": "${prompt || 'A majestic medieval castle on a floating island...'}",
    "parameters": {
        "negative_prompt": "${negativePrompt}",
        "guidance_scale": ${guidanceScale},
        "num_inference_steps": ${inferenceSteps},
        "width": ${aspectRatio === '16:9' ? 1024 : aspectRatio === '9:16' ? 576 : 1024},
        "height": ${aspectRatio === '16:9' ? 576 : aspectRatio === '9:16' ? 1024 : 1024}
    }
}

image_bytes = query_cosmos(payload)
with open("cosmos3_output.jpg", "wb") as f:
    f.write(image_bytes)
print("✨ 影像生成成功，已儲存為 cosmos3_output.jpg")
`, 'Python 程式碼')}
                    className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>複製程式碼</span>
                  </button>
                </div>
                <pre className="bg-slate-900 p-3 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto leading-relaxed flex-1 select-all">
{`import requests

API_URL = "https://api-inference.huggingface.co/models/nvidia/Cosmos3-Super-Text2Image"
headers = {"Authorization": "Bearer ${hfToken || 'YOUR_HF_TOKEN_HERE'}"}

payload = {
    "inputs": "${prompt || 'A majestic medieval castle...'}",
    "parameters": {
        "negative_prompt": "${negativePrompt}",
        "guidance_scale": ${guidanceScale},
        "num_inference_steps": ${inferenceSteps}
    }
}

response = requests.post(API_URL, headers=headers, json=payload)
with open("cosmos3_output.jpg", "wb") as f:
    f.write(response.content)
print("✨ 影像生成成功")`}
                </pre>
              </div>

              {/* cURL 端點請求指令 */}
              <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#76b900] flex items-center space-x-1.5">
                    <Terminal className="w-3.5 h-3.5" />
                    <span>cURL 指令 (終端機命令)</span>
                  </span>
                  <button
                    onClick={() => handleCopyText(
`curl https://api-inference.huggingface.co/models/nvidia/Cosmos3-Super-Text2Image \\
  -X POST \\
  -H "Authorization: Bearer ${hfToken || 'YOUR_HF_TOKEN_HERE'}" \\
  -H "Content-Type: application/json" \\
  -d '{"inputs": "${prompt.replace(/'/g, "'\\''")||'A majestic castle...'}", "parameters": {"guidance_scale": ${guidanceScale}, "num_inference_steps": ${inferenceSteps}}}' \\
  --output cosmos3_image.jpg`, 'cURL 指令')}
                    className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>複製指令</span>
                  </button>
                </div>
                <pre className="bg-slate-900 p-3 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto leading-relaxed flex-1 select-all">
{`curl https://api-inference.huggingface.co/models/nvidia/Cosmos3-Super-Text2Image \\
  -X POST \\
  -H "Authorization: Bearer ${hfToken || 'YOUR_HF_TOKEN_HERE'}" \\
  -H "Content-Type: application/json" \\
  -d '{"inputs": "${prompt || 'A majestic castle...'}",
       "parameters": {
         "guidance_scale": ${guidanceScale},
         "num_inference_steps": ${inferenceSteps}
       }}' \\
  --output cosmos3_image.jpg`}
                </pre>
              </div>

            </div>

            {/* 本地端部署與微調小貼士 */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs font-bold text-[#76b900] block mb-1.5">🎓 學科小筆記：如何本地微調 (Fine-tuning) 與推演 (vLLM-Omni)？</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                NVIDIA 隨 Cosmos 3 推出了專門的輕量級推演容器 <code>vllm-omni:cosmos3</code>。對於具備頂級硬體設備（如 8x H100 節點）的高級研究室，可以使用該容器啟動相容 OpenAI 的 API 伺服器，並以此前端網頁更換基本 API Endpoint 網址，即可輕鬆實現完全自主控制的校園 AI 圖像生成系統！
              </p>
            </div>

          </div>
        )}

      </main>

      {/* 底部 Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/60 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 Cosmos 3 AI 繪圖工坊. 基於開源 AI 科普教學專題</p>
          <div className="flex space-x-4">
            <a href="https://huggingface.co/nvidia/Cosmos3-Super-Text2Image" target="_blank" rel="noreferrer" className="hover:text-white flex items-center space-x-1">
              <span>Hugging Face 模型卡</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>•</span>
            <a href="https://github.com/nvidia/cosmos" target="_blank" rel="noreferrer" className="hover:text-white flex items-center space-x-1">
              <span>NVIDIA Cosmos GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>

    </div>
  );
}
