"""
Outlook連携モジュール【ICS版・Azureのアプリ登録が不要】。

outlook_calendar_service.py（Microsoft Graph API版）はAzure Portalでの
アプリ登録・OAuth認証が必要で手間がかかる。こちらはその代わりに、
Outlookの「カレンダーを公開」機能で発行されるICS形式のURL、または
エクスポートした .ics ファイルを読み込むことで、本物の予定データを
表示する。Azure Portalでの作業は一切不要。

============================================================
方法1: 公開URLを使う（おすすめ。発表中もその場で最新の予定を取得できる）
============================================================
1. https://outlook.live.com/calendar/ を開く
2. 画面右上の歯車アイコン →「すべての設定を表示」→
   「カレンダー」→「共有カレンダー」
3. 「カレンダーを公開する」で対象のカレンダーと権限
   （「すべての詳細を表示できます」を推奨）を選び、「公開」をクリック
4. 表示される「ICS」形式のリンクをコピーする
   （例: https://outlook.live.com/owa/calendar/xxxxxxxx/xxxxxxxx/calendar.ics）
5. .streamlit/secrets.toml に以下を追記する:

       OUTLOOK_ICS_URL = "コピーしたリンク"

   ※このリンクを知っていれば誰でもカレンダーの中身を見られてしまうので
     （個人を特定できるURLではないが、予定の内容は見える）、
     secrets.toml は必ず .gitignore 済みの状態でコミットしないこと。
     発表後にカレンダーの公開を停止すれば、リンクは無効になる。

============================================================
方法2: .icsファイルをアップロードする（一番簡単。ネット接続も不要）
============================================================
1. Outlook on the web の設定 →「カレンダー」→
   「表示、印刷、共有」などから、カレンダーを .ics 形式でエクスポート
   （デスクトップ版Outlookなら「ファイル」→「カレンダーの保存」でも可）
2. 「余白時間を登録」画面の連携先で「Outlook（ICS・かんたん版）」を選ぶと
   ファイルアップロード欄が表示されるので、そこでエクスポートした
   .ics ファイルを選択する

============================================================
必要パッケージ
============================================================
pip install icalendar
"""

from datetime import datetime

import requests
import streamlit as st

try:
    from icalendar import Calendar
except ImportError:
    Calendar = None

ICS_URL_SECRET_KEY = "OUTLOOK_ICS_URL"
_UPLOAD_SESSION_KEY = "_outlook_ics_bytes"


def _get_ics_url():
    try:
        if ICS_URL_SECRET_KEY in st.secrets:
            return st.secrets[ICS_URL_SECRET_KEY]
    except Exception:
        pass
    return ""


def uses_url():
    """公開URLが設定済みかどうか（設定済みならアップロード欄は不要）。"""
    return bool(_get_ics_url())


def render_upload_widget():
    """
    .icsファイルのアップロードUI。calendar_widget.py から、
    公開URLが未設定のときだけ呼び出される。
    アップロードされた内容は session_state にキャッシュし、
    get_busy_events() から参照する。
    """
    uploaded = st.file_uploader(
        "Outlookからエクスポートした .ics ファイルをアップロード",
        type=["ics"],
        key="outlook_ics_upload",
    )
    if uploaded is not None:
        st.session_state[_UPLOAD_SESSION_KEY] = uploaded.getvalue()
        st.caption(f"✅「{uploaded.name}」を読み込みました。")


def _parse_ics_bytes(ics_bytes, target_date):
    if Calendar is None:
        raise RuntimeError(
            "icalendar パッケージがインストールされていません。"
            "`pip install icalendar` を実行してから再度お試しください。"
        )

    cal = Calendar.from_ical(ics_bytes)

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("dtstart").dt
        dtend = component.get("dtend").dt

        # 終日予定（date型。時刻情報を持たない）はその日の枠を丸ごと
        # 潰してしまうので、空き時間計算からは除外する
        if not isinstance(dtstart, datetime):
            continue

        # タイムゾーン付きの場合はローカル（このPCの）時刻に変換する。
        # Outlookエクスポートのタイムゾーン情報がうまく解決できない場合に
        # 備えて、失敗したらtzinfoを外してそのまま使う（デモを止めないため）。
        if dtstart.tzinfo is not None:
            try:
                dtstart = dtstart.astimezone().replace(tzinfo=None)
            except Exception:
                dtstart = dtstart.replace(tzinfo=None)
        if dtend.tzinfo is not None:
            try:
                dtend = dtend.astimezone().replace(tzinfo=None)
            except Exception:
                dtend = dtend.replace(tzinfo=None)

        if dtstart.date() != target_date:
            continue

        summary = str(component.get("summary", "") or "(無題の予定)")
        events.append(
            {
                "start": dtstart.strftime("%H:%M"),
                "end": dtend.strftime("%H:%M"),
                "summary": summary,
            }
        )

    events.sort(key=lambda e: e["start"])
    return events


def get_busy_events(target_date):
    """
    指定日のOutlook予定を取得する【ICS版・本物のデータ】。

    戻り値: [{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]
    google_calendar_service / outlook_calendar_service と同じ形式。

    優先順位:
      1. .streamlit/secrets.toml に OUTLOOK_ICS_URL が設定されていれば、
         そこから毎回最新の予定を取得する
      2. 設定されていなければ、アップロード済みの .ics ファイル
         （session_state）から取得する
      3. どちらも無ければエラーメッセージを出す
    """
    url = _get_ics_url()
    if url:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return _parse_ics_bytes(resp.content, target_date)

    ics_bytes = st.session_state.get(_UPLOAD_SESSION_KEY)
    if ics_bytes:
        return _parse_ics_bytes(ics_bytes, target_date)

    raise RuntimeError(
        "カレンダーの公開URLが未設定で、.icsファイルもアップロードされていません。"
        "上の「.icsファイルをアップロード」から予定表を読み込むか、"
        "secrets.toml に OUTLOOK_ICS_URL を設定してください。"
    )
