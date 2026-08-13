"""「龍蝦」養成班 — Google Workspace OAuth 2.0 授權

第一次執行會開啟瀏覽器要你登入並同意授權，成功後在同目錄產生 token.json，
之後其他範例（calendar / sheets / gmail）都直接沿用這個 token。

    pip install -r requirements.txt
    python google_auth.py

前置作業（見 README 第 6.2 節）：
    1. Google Cloud Console 建立專案並啟用 Calendar / Sheets / Gmail API
    2. OAuth 同意畫面設為「外部」，並把自己的 Gmail 加入「測試使用者」
    3. 建立「電腦版應用程式」OAuth 用戶端 ID，下載 JSON 改名 credentials.json
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# 最小權限原則：只要用得到的才放進來。
# 課堂上先用可讀寫的範圍做完實作，回家後請改成 .readonly。
SCOPES = [
    "https://www.googleapis.com/auth/calendar",            # 讀 + 寫行事曆
    "https://www.googleapis.com/auth/spreadsheets",        # 讀 + 寫試算表
    "https://www.googleapis.com/auth/drive.file",          # 只能碰本程式建立的檔案
    "https://www.googleapis.com/auth/gmail.readonly",      # Gmail 只讀，不給寄信權限
]


def get_credentials(scopes: list[str] | None = None) -> Credentials:
    """取得可用的憑證：有 token 就沿用，過期就自動更新，都沒有才走授權流程。"""
    scopes = scopes or SCOPES
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), scopes)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        # Access Token 約一小時就過期，用 Refresh Token 換新的，不用再登入
        print("→ Access Token 已過期，使用 Refresh Token 更新…")
        creds.refresh(Request())
    else:
        if not CREDENTIALS_FILE.exists():
            raise SystemExit(
                f"\n找不到 {CREDENTIALS_FILE.name}\n\n"
                "請先到 Google Cloud Console 建立「電腦版應用程式」OAuth 用戶端 ID，\n"
                "下載 JSON 後改名為 credentials.json 放在這個資料夾。\n"
                "詳細步驟見 README 第 6.2 節。\n"
            )
        print("→ 開啟瀏覽器進行授權…")
        print("  （出現「應用程式未經驗證」是正常的：點『進階』→『前往…（不安全）』）")
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), scopes)
        creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    # token.json 內含 Refresh Token，效力等同密碼，絕不可上傳到 Git
    TOKEN_FILE.chmod(0o600)
    print(f"✓ 憑證已儲存至 {TOKEN_FILE.name}（權限 600，請勿外流）")
    return creds


def main() -> None:
    creds = get_credentials()

    # 用最輕量的呼叫確認 token 真的能用
    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=creds)
    profile = service.calendarList().get(calendarId="primary").execute()

    print()
    print("✅ 授權成功")
    print(f"   主要行事曆：{profile.get('summary')}")
    print(f"   時區：{profile.get('timeZone')}")
    print()
    print("接著可以執行：")
    print("   python calendar_demo.py")
    print("   python sheets_demo.py")
    print("   python gmail_digest.py")


if __name__ == "__main__":
    main()
