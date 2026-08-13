#!/usr/bin/env bash
# 「龍蝦」養成班 — 上課前環境檢查（macOS / Linux）
# 用法： bash 260903/scripts/check-env.sh

set -uo pipefail

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'
pass=0; warn=0; fail=0

ok()   { echo -e "  ${GREEN}✓${NC} $1"; pass=$((pass+1)); }
warning() { echo -e "  ${YELLOW}!${NC} $1"; warn=$((warn+1)); }
bad()  { echo -e "  ${RED}✗${NC} $1"; fail=$((fail+1)); }

echo ""
echo "🦞 龍蝦養成班 — 環境檢查"
echo "================================================"

# ── 作業系統 ────────────────────────────────────────
echo ""
echo "▸ 作業系統"
OS="$(uname -s)"
case "$OS" in
  Darwin)
    ok "macOS $(sw_vers -productVersion) ($(uname -m))"
    [ "$(uname -m)" = "arm64" ] && ok "Apple Silicon — 統一記憶體，跑本地模型有優勢"
    ;;
  Linux)
    ok "Linux $(uname -r)"
    if command -v nvidia-smi >/dev/null 2>&1; then
      ok "NVIDIA GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)"
    else
      warning "找不到 nvidia-smi — 將以 CPU 推論，請使用 4B 以下模型"
    fi
    ;;
  *) warning "未預期的系統：$OS" ;;
esac

# ── 記憶體 ──────────────────────────────────────────
echo ""
echo "▸ 記憶體"
if [ "$OS" = "Darwin" ]; then
  RAM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
else
  RAM_GB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
fi
if   [ "$RAM_GB" -ge 32 ]; then ok "${RAM_GB} GB RAM — 可跑到 14B~20B"
elif [ "$RAM_GB" -ge 16 ]; then ok "${RAM_GB} GB RAM — 課程主力 7B/8B 沒問題"
elif [ "$RAM_GB" -ge 8  ]; then warning "${RAM_GB} GB RAM — 請使用 3B/4B 量化模型，不要硬跑 8B"
else                            bad "${RAM_GB} GB RAM — 低於最低需求，建議改用雲端模型上課"
fi

# ── 磁碟空間 ────────────────────────────────────────
echo ""
echo "▸ 磁碟空間"
AVAIL_GB=$(df -Pg "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' || df -P "$HOME" | awk 'NR==2 {print int($4/1048576)}')
if [ "${AVAIL_GB:-0}" -ge 30 ]; then ok "可用 ${AVAIL_GB} GB"
elif [ "${AVAIL_GB:-0}" -ge 15 ]; then warning "可用 ${AVAIL_GB} GB — 只夠 1~2 個模型，請先清空間"
else bad "可用 ${AVAIL_GB} GB — 模型下載會失敗，請清出 30 GB 以上"
fi

# ── Node.js ────────────────────────────────────────
echo ""
echo "▸ Node.js（OpenClaw 需要 22.22.3+ / 24.15+ / 25.9+）"
if command -v node >/dev/null 2>&1; then
  NODE_RAW="$(node --version)"; NODE_V="${NODE_RAW#v}"
  MAJOR="${NODE_V%%.*}"; REST="${NODE_V#*.}"; MINOR="${REST%%.*}"; PATCH="${NODE_V##*.}"
  node_ok=0
  if   [ "$MAJOR" -ge 26 ]; then node_ok=1
  elif [ "$MAJOR" -eq 25 ] && [ "$MINOR" -ge 9 ]; then node_ok=1
  elif [ "$MAJOR" -eq 24 ] && [ "$MINOR" -ge 15 ]; then node_ok=1
  elif [ "$MAJOR" -eq 22 ] && { [ "$MINOR" -gt 22 ] || { [ "$MINOR" -eq 22 ] && [ "$PATCH" -ge 3 ]; }; }; then node_ok=1
  fi
  if [ "$node_ok" -eq 1 ]; then ok "Node $NODE_RAW"
  else bad "Node $NODE_RAW 版本不符 — 請執行 nvm install 26 && nvm use 26"; fi
else
  bad "找不到 Node.js — 請安裝 https://nodejs.org/ 或使用 nvm"
fi

# ── Python ─────────────────────────────────────────
echo ""
echo "▸ Python（需要 3.10+）"
PY=""
command -v python3 >/dev/null 2>&1 && PY=python3
[ -z "$PY" ] && command -v python >/dev/null 2>&1 && PY=python
if [ -n "$PY" ]; then
  PV="$($PY -c 'import sys; print("%d.%d"%sys.version_info[:2])')"
  if $PY -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
    ok "Python $PV ($PY)"
  else
    bad "Python $PV 太舊 — 需要 3.10 以上"
  fi
else
  bad "找不到 Python — 請安裝 https://www.python.org/downloads/"
fi

# ── 其他工具 ────────────────────────────────────────
echo ""
echo "▸ 其他工具"
command -v git    >/dev/null 2>&1 && ok "git $(git --version | awk '{print $3}')" || bad "找不到 git"
command -v curl   >/dev/null 2>&1 && ok "curl" || bad "找不到 curl"
command -v docker >/dev/null 2>&1 && ok "docker（可用 Docker 版 Open WebUI）" \
                                  || warning "沒有 Docker — Open WebUI 改用 pip 安裝即可"
command -v ollama >/dev/null 2>&1 && ok "ollama $(ollama --version 2>/dev/null | head -1)" \
                                  || warning "尚未安裝 Ollama（第二堂會裝）"
command -v openclaw >/dev/null 2>&1 && ok "openclaw 已安裝" \
                                    || warning "尚未安裝 OpenClaw（第四堂會裝）"

# ── 埠檢查 ──────────────────────────────────────────
echo ""
echo "▸ 埠是否被佔用"
check_port() {
  if command -v lsof >/dev/null 2>&1 && lsof -i ":$1" -sTCP:LISTEN >/dev/null 2>&1; then
    warning "埠 $1（$2）已被佔用 — 若非 $2 本身請先關閉"
  else
    ok "埠 $1（$2）可用"
  fi
}
check_port 11434 "Ollama"
check_port 18789 "OpenClaw Gateway"
check_port 3000  "Open WebUI"

# ── 總結 ────────────────────────────────────────────
echo ""
echo "================================================"
echo -e "結果： ${GREEN}${pass} 通過${NC} / ${YELLOW}${warn} 提醒${NC} / ${RED}${fail} 失敗${NC}"
if [ "$fail" -gt 0 ]; then
  echo ""
  echo "❗ 有 ${fail} 項未通過，請在上課前處理完畢。"
  exit 1
fi
echo ""
echo "✅ 環境沒問題！接著執行： bash 260903/scripts/setup-ollama.sh"
