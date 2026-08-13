"""「龍蝦」養成班 — 第五堂實作：串接 Google Sheets

建立一份試算表、寫入資料、再讀回來驗證。
典型用途：讓 Agent 把整理好的資料（信件分類、會議待辦）自動記錄下來。

    python sheets_demo.py
    python sheets_demo.py --id <既有試算表ID>    # 附加到既有表格
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google_auth import get_credentials

TAIPEI = timezone(timedelta(hours=8))
HEADER = ["時間", "類別", "項目", "負責人", "狀態"]


def _service():
    return build("sheets", "v4", credentials=get_credentials())


def create_spreadsheet(title: str) -> str:
    """建立試算表，回傳 spreadsheetId。"""
    body = {
        "properties": {"title": title, "locale": "zh_TW", "timeZone": "Asia/Taipei"},
        "sheets": [{"properties": {"title": "工作記錄"}}],
    }
    sheet = _service().spreadsheets().create(body=body, fields="spreadsheetId").execute()
    return sheet["spreadsheetId"]


def append_rows(spreadsheet_id: str, rows: list[list[str]], sheet_name: str = "工作記錄") -> int:
    """把資料附加到表格最後一列，回傳實際寫入的列數。"""
    result = (
        _service()
        .spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:E",
            valueInputOption="USER_ENTERED",   # 讓 Google 解析日期/數字格式
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        )
        .execute()
    )
    return result.get("updates", {}).get("updatedRows", 0)


def read_rows(spreadsheet_id: str, sheet_name: str = "工作記錄") -> list[list[str]]:
    """讀回整張表。"""
    result = (
        _service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:E")
        .execute()
    )
    return result.get("values", [])


def format_header(spreadsheet_id: str) -> None:
    """把第一列做成粗體深色標題並凍結，純粹是為了 Demo 好看。"""
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.11, "green": 0.13, "blue": 0.18},
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    _service().spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Sheets 實作範例")
    parser.add_argument("--id", help="既有試算表 ID；不給就建立新的")
    args = parser.parse_args()

    now = datetime.now(TAIPEI)

    try:
        if args.id:
            sheet_id = args.id
            print(f"\n📊 使用既有試算表 {sheet_id}")
        else:
            title = f"龍蝦養成班 工作記錄 {now:%Y-%m-%d}"
            print(f"\n📊 建立試算表「{title}」…")
            sheet_id = create_spreadsheet(title)
            append_rows(sheet_id, [HEADER])
            format_header(sheet_id)
            print(f"✓ 建立完成，ID：{sheet_id}")

        # ── 寫入 ────────────────────────────────────
        rows = [
            [f"{now:%Y-%m-%d %H:%M}", "環境", "Ollama + Open WebUI 架設完成", "我", "完成"],
            [f"{now:%Y-%m-%d %H:%M}", "Agent", "OpenClaw 串接本地模型", "我", "完成"],
            [f"{now:%Y-%m-%d %H:%M}", "串接", "Google Calendar 讀寫", "我", "進行中"],
        ]
        written = append_rows(sheet_id, rows)
        print(f"✓ 寫入 {written} 列")

        # ── 讀回驗證 ────────────────────────────────
        print("\n📖 讀回表格內容：")
        print("─" * 66)
        for row in read_rows(sheet_id):
            padded = row + [""] * (len(HEADER) - len(row))
            print("  " + " │ ".join(f"{c[:16]:<16}" for c in padded))

        print(f"\n🔗 https://docs.google.com/spreadsheets/d/{sheet_id}")

    except HttpError as err:
        print(f"\n❌ API 錯誤：{err}")
        if err.resp.status == 403:
            print("   403 通常是 Sheets API 沒啟用，或 scope 少了 spreadsheets。")
            print("   改了 SCOPES 之後要刪掉 token.json 重新授權。")


if __name__ == "__main__":
    main()
