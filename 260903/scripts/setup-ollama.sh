#!/usr/bin/env bash
# 「龍蝦」養成班 — 預先下載模型
# 請在上課前於家中網路執行，教室 Wi-Fi 不夠所有人同時下載。
# 用法： bash 260903/scripts/setup-ollama.sh

set -uo pipefail

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'

echo ""
echo "🦞 龍蝦養成班 — 模型預先下載"
echo "================================================"

# ── 確認 Ollama ─────────────────────────────────────
if ! command -v ollama >/dev/null 2>&1; then
  echo -e "${YELLOW}找不到 ollama，正在安裝…${NC}"
  case "$(uname -s)" in
    Darwin|Linux) curl -fsSL https://ollama.com/install.sh | sh ;;
    *) echo "請手動下載： https://ollama.com/download"; exit 1 ;;
  esac
fi
echo -e "${GREEN}✓${NC} ollama $(ollama --version 2>/dev/null | head -1)"

# ── 確認服務有起來 ──────────────────────────────────
if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "  啟動 Ollama 服務…"
  (ollama serve >/dev/null 2>&1 &)
  for _ in $(seq 1 15); do
    curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 1
  done
fi
curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1 \
  && echo -e "${GREEN}✓${NC} Ollama 服務運作中 (:11434)" \
  || { echo "Ollama 服務起不來，請手動執行 ollama serve"; exit 1; }

# ── 依記憶體挑模型 ──────────────────────────────────
if [ "$(uname -s)" = "Darwin" ]; then
  RAM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
else
  RAM_GB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
fi

echo ""
echo "偵測到 ${RAM_GB} GB RAM"

if [ "$RAM_GB" -ge 32 ]; then
  MODELS=("qwen3:8b" "qwen3:14b" "llama3.2:3b" "nomic-embed-text")
  echo "→ 下載 8B + 14B 組合"
elif [ "$RAM_GB" -ge 16 ]; then
  MODELS=("qwen3:8b" "llama3.2:3b" "nomic-embed-text")
  echo "→ 下載 8B 主力 + 3B 備援"
else
  MODELS=("qwen3:4b" "llama3.2:3b" "nomic-embed-text")
  echo "→ 記憶體有限，只下載 4B 以下模型"
fi

echo ""
echo "預計下載 ${#MODELS[@]} 個模型，總計約 6~15 GB，請保持網路連線。"
echo ""

# ── 開始下載 ────────────────────────────────────────
for m in "${MODELS[@]}"; do
  echo "──────────────────────────────────────────"
  echo "▸ ollama pull $m"
  if ollama pull "$m"; then
    echo -e "${GREEN}✓${NC} $m 完成"
  else
    echo -e "${YELLOW}!${NC} $m 下載失敗 — 可能是模型標籤已更新"
    echo "  請到 https://ollama.com/library 查詢目前可用的標籤後手動下載"
  fi
done

# ── 驗證 ────────────────────────────────────────────
echo ""
echo "================================================"
echo "已安裝的模型："
ollama list

echo ""
echo "測試對話（qwen3 或第一個可用模型）："
FIRST="$(ollama list | awk 'NR==2 {print $1}')"
if [ -n "$FIRST" ]; then
  echo "  ollama run $FIRST \"用一句話介紹你自己\""
  ollama run "$FIRST" "用一句話介紹你自己"
fi

echo ""
echo -e "${GREEN}✅ 準備完成，上課時直接開始第二堂的 Open WebUI。${NC}"
echo ""
echo "小提醒："
echo "  • nomic-embed-text 是嵌入模型，課後玩 RAG 會用到"
echo "  • 空間不夠時用 ollama rm <model> 刪掉不用的"
