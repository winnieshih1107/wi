# 「龍蝦」養成班 — 上課前環境檢查（Windows PowerShell）
# 用法： powershell -ExecutionPolicy Bypass -File 260903\scripts\check-env.ps1

$script:pass = 0; $script:warn = 0; $script:fail = 0

function Ok($m)   { Write-Host "  [OK] $m"   -ForegroundColor Green;  $script:pass++ }
function Warn($m) { Write-Host "  [!]  $m"   -ForegroundColor Yellow; $script:warn++ }
function Bad($m)  { Write-Host "  [X]  $m"   -ForegroundColor Red;    $script:fail++ }

Write-Host ""
Write-Host "龍蝦養成班 — 環境檢查"
Write-Host "================================================"

# ── 作業系統 ────────────────────────────────────────
Write-Host ""
Write-Host "> 作業系統"
$os = Get-CimInstance Win32_OperatingSystem
Ok "$($os.Caption) ($($os.OSArchitecture))"

$gpus = Get-CimInstance Win32_VideoController
$hasDedicated = $false
foreach ($g in $gpus) {
    $vramGB = [math]::Round($g.AdapterRAM / 1GB, 1)
    if ($g.Name -match 'NVIDIA|Radeon RX|Arc') {
        Ok "獨立顯卡：$($g.Name) (~$vramGB GB VRAM)"
        $hasDedicated = $true
    }
}
if (-not $hasDedicated) { Warn "沒有偵測到獨立顯卡 — 將以 CPU 推論，請使用 3B/4B 模型" }

# ── 記憶體 ──────────────────────────────────────────
Write-Host ""
Write-Host "> 記憶體"
$ramGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 0)
if     ($ramGB -ge 32) { Ok   "$ramGB GB RAM — 可跑到 14B~20B" }
elseif ($ramGB -ge 16) { Ok   "$ramGB GB RAM — 課程主力 7B/8B 沒問題" }
elseif ($ramGB -ge 8)  { Warn "$ramGB GB RAM — 請使用 3B/4B 量化模型，不要硬跑 8B" }
else                   { Bad  "$ramGB GB RAM — 低於最低需求，建議改用雲端模型上課" }

# ── 磁碟空間 ────────────────────────────────────────
Write-Host ""
Write-Host "> 磁碟空間"
$drive = (Get-Item $env:USERPROFILE).PSDrive.Name
$freeGB = [math]::Round((Get-PSDrive $drive).Free / 1GB, 0)
if     ($freeGB -ge 30) { Ok   "$($drive): 可用 $freeGB GB" }
elseif ($freeGB -ge 15) { Warn "$($drive): 可用 $freeGB GB — 只夠 1~2 個模型，請先清空間" }
else                    { Bad  "$($drive): 可用 $freeGB GB — 模型下載會失敗，請清出 30 GB 以上" }

# ── Node.js ────────────────────────────────────────
Write-Host ""
Write-Host "> Node.js（OpenClaw 需要 22.22.3+ / 24.15+ / 25.9+）"
if (Get-Command node -ErrorAction SilentlyContinue) {
    $raw = (node --version).Trim()
    $v = [version]($raw.TrimStart('v'))
    $nodeOk = ($v.Major -ge 26) -or
              ($v.Major -eq 25 -and $v.Minor -ge 9) -or
              ($v.Major -eq 24 -and $v.Minor -ge 15) -or
              ($v.Major -eq 22 -and $v -ge [version]'22.22.3')
    if ($nodeOk) { Ok "Node $raw" }
    else { Bad "Node $raw 版本不符 — 請用 nvm-windows 安裝 Node 26" }
} else {
    Bad "找不到 Node.js — 請安裝 https://nodejs.org/"
}

# ── Python ─────────────────────────────────────────
Write-Host ""
Write-Host "> Python（需要 3.10+）"
$pyCmd = $null
foreach ($c in @('python', 'py')) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $pyCmd = $c; break }
}
if ($pyCmd) {
    $pv = (& $pyCmd -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null)
    if ($pv -and [version]$pv -ge [version]'3.10') { Ok "Python $pv" }
    else { Bad "Python $pv 太舊 — 需要 3.10 以上" }
} else {
    Bad "找不到 Python — 請安裝 https://www.python.org/downloads/（安裝時勾選 Add to PATH）"
}

# ── 其他工具 ────────────────────────────────────────
Write-Host ""
Write-Host "> 其他工具"
if (Get-Command git      -ErrorAction SilentlyContinue) { Ok "git" }      else { Bad "找不到 git" }
if (Get-Command docker   -ErrorAction SilentlyContinue) { Ok "docker（可用 Docker 版 Open WebUI）" } else { Warn "沒有 Docker — Open WebUI 改用 pip 安裝即可" }
if (Get-Command ollama   -ErrorAction SilentlyContinue) { Ok "ollama 已安裝" }   else { Warn "尚未安裝 Ollama（第二堂會裝）" }
if (Get-Command openclaw -ErrorAction SilentlyContinue) { Ok "openclaw 已安裝" } else { Warn "尚未安裝 OpenClaw（第四堂會裝）" }

# ── 埠檢查 ──────────────────────────────────────────
Write-Host ""
Write-Host "> 埠是否被佔用"
function Check-Port($port, $name) {
    $inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($inUse) { Warn "埠 $port（$name）已被佔用 — 若非 $name 本身請先關閉" }
    else        { Ok   "埠 $port（$name）可用" }
}
Check-Port 11434 "Ollama"
Check-Port 18789 "OpenClaw Gateway"
Check-Port 3000  "Open WebUI"

# ── 總結 ────────────────────────────────────────────
Write-Host ""
Write-Host "================================================"
Write-Host "結果： $script:pass 通過 / $script:warn 提醒 / $script:fail 失敗"
if ($script:fail -gt 0) {
    Write-Host ""
    Write-Host "有 $script:fail 項未通過，請在上課前處理完畢。" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "環境沒問題！接著請預先下載模型：ollama pull qwen3:8b" -ForegroundColor Green
