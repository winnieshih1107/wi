"""「龍蝦」養成班 — 第五堂實作：串接 Google Calendar

示範兩件事：讀取今天的行程、建立一筆事件。
這兩個函式可以直接包成 OpenClaw 的 Tool 給 Agent 呼叫。

    python calendar_demo.py            # 讀今天行程 + 建立測試事件
    python calendar_demo.py --read     # 只讀，不寫
"""

from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google_auth import get_credentials

TAIPEI = timezone(timedelta(hours=8))
CALENDAR_ID = "primary"


def _service():
    return build("calendar", "v3", credentials=get_credentials())


def list_today_events() -> list[dict]:
    """回傳今天（台北時間）的所有事件。"""
    now = datetime.now(TAIPEI)
    start = datetime.combine(now.date(), time.min, tzinfo=TAIPEI)
    end = start + timedelta(days=1)

    result = (
        _service()
        .events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,       # 把週期性事件展開成單筆
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def create_event(
    summary: str,
    start: datetime,
    duration_minutes: int = 60,
    description: str = "",
    location: str = "",
) -> dict:
    """建立一筆事件，回傳建立結果（含可點擊的 htmlLink）。"""
    body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Taipei"},
        "end": {
            "dateTime": (start + timedelta(minutes=duration_minutes)).isoformat(),
            "timeZone": "Asia/Taipei",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": 10}],
        },
    }
    return _service().events().insert(calendarId=CALENDAR_ID, body=body).execute()


def _format(event: dict) -> str:
    start = event["start"].get("dateTime", event["start"].get("date"))
    if "T" in start:
        clock = datetime.fromisoformat(start).astimezone(TAIPEI).strftime("%H:%M")
    else:
        clock = "整天"
    return f"  {clock:>5}  {event.get('summary', '(無標題)')}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Calendar 實作範例")
    parser.add_argument("--read", action="store_true", help="只讀取，不建立事件")
    args = parser.parse_args()

    try:
        # ── 讀 ──────────────────────────────────────
        print(f"\n📅 今天（{datetime.now(TAIPEI):%Y-%m-%d}）的行程")
        print("─" * 46)
        events = list_today_events()
        if events:
            for e in events:
                print(_format(e))
            print(f"\n  共 {len(events)} 筆")
        else:
            print("  （今天沒有行程）")

        if args.read:
            return

        # ── 寫 ──────────────────────────────────────
        tomorrow_10am = datetime.combine(
            datetime.now(TAIPEI).date() + timedelta(days=1), time(10, 0), tzinfo=TAIPEI
        )
        print("\n📝 建立測試事件…")
        created = create_event(
            summary="🦞 龍蝦養成班 — Agent 建立的測試事件",
            start=tomorrow_10am,
            duration_minutes=30,
            description="這筆事件由 Google Calendar API 建立，確認寫入權限正常。",
            location="逢甲大學行政一館 204 室",
        )
        print(f"✓ 已建立：{created.get('summary')}")
        print(f"  時間：{tomorrow_10am:%Y-%m-%d %H:%M}")
        print(f"  連結：{created.get('htmlLink')}")
        print("\n請到 Google Calendar 網頁確認，確認完可以直接刪掉。")

    except HttpError as err:
        print(f"\n❌ API 錯誤：{err}")
        if err.resp.status == 403:
            print("   403 通常是 Calendar API 沒啟用，或 scope 不含寫入權限。")
            print("   改了 SCOPES 之後要刪掉 token.json 重新授權。")
        elif err.resp.status == 401:
            print("   401 代表憑證失效，刪掉 token.json 重跑 google_auth.py。")


if __name__ == "__main__":
    main()
