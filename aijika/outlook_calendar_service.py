"""
Outlook（Microsoft Graph）連携モジュール【本物のAPIを呼び出す版】。

個人のOutlook（outlook.com / hotmail 等）アカウントの予定表から、
その日の予定を取得する。google_calendar_service.py と同じ形式
（[{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]）で
予定を返すので、views/free_time_form.py 側はどちらの連携先を
使っても同じコードで扱える。

認証には MSAL（Microsoft Authentication Library for Python）を使う。
初回はブラウザが自動で開き、Microsoftアカウントへのログインを求められる。
ログイン結果はローカルの token_cache.bin にキャッシュされるため、
2回目以降（＝発表本番）は自動的にログイン済みの状態になる。
発表直前に一度この画面を開いてログインを済ませておくこと。

============================================================
事前準備（Azure Portalでの作業・各自のMicrosoftアカウントで実施）
============================================================
1. https://portal.azure.com/ にアクセスし、
   「Microsoft Entra ID」→「アプリの登録」→「新規登録」
2. 名前は任意（例: 空いてる時間どうする-Outlook連携）
3. 「サポートされているアカウントの種類」で
   「個人の Microsoft アカウントのみ」を選択
   （会社のMicrosoft 365アカウントを使いたい場合は選択肢が変わるので要相談）
4. 「リダイレクトURI」でプラットフォーム「パブリック クライアント/ネイティブ
   (モバイルとデスクトップ)」を選び、`http://localhost` を追加して登録
5. 登録後に表示される「アプリケーション (クライアント) ID」をコピー
6. 「APIのアクセス許可」→「アクセス許可の追加」→「Microsoft Graph」→
   「委任されたアクセス許可」→ `Calendars.Read` を追加
   （個人アカウント利用なら管理者の承認は不要）

============================================================
このアプリ側の設定
============================================================
1. `pip install msal` を実行（requirements.txt に追加済み）
2. プロジェクト直下に `.streamlit/secrets.toml` を作成し、以下を記入
   （このファイルは .gitignore 済みなのでコミットされない）:

       OUTLOOK_CLIENT_ID = "手順5でコピーしたクライアントID"

3. `streamlit run app.py` を実行し、「余白時間を登録」画面で
   連携先を「Outlook（本物）」に切り替えるとブラウザでログインを求められる
"""

import os
from datetime import datetime, timedelta

import requests
import streamlit as st

AUTHORITY = "https://login.microsoftonline.com/consumers"  # 個人Microsoftアカウント向け
SCOPES = ["Calendars.Read"]
TOKEN_CACHE_PATH = "outlook_token_cache.bin"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


def _get_client_id():
    try:
        if "OUTLOOK_CLIENT_ID" in st.secrets:
            return st.secrets["OUTLOOK_CLIENT_ID"]
    except Exception:
        pass
    return os.environ.get("OUTLOOK_CLIENT_ID", "")


def _load_token_cache(cache_cls):
    cache = cache_cls()
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def _save_token_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_PATH, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def _get_access_token():
    """
    Microsoft Graph 用のアクセストークンを取得する。
    2回目以降はローカルキャッシュから、初回や期限切れ時はブラウザでログイン。
    """
    try:
        from msal import PublicClientApplication, SerializableTokenCache
    except ImportError as exc:
        raise RuntimeError(
            "msal パッケージがインストールされていません。"
            "`pip install msal` を実行してから再度お試しください。"
        ) from exc

    client_id = _get_client_id()
    if not client_id:
        raise RuntimeError(
            ".streamlit/secrets.toml に OUTLOOK_CLIENT_ID が設定されていません。"
            "Azure Portalで発行したクライアントIDを設定してください。"
        )

    cache = _load_token_cache(SerializableTokenCache)
    app = PublicClientApplication(client_id, authority=AUTHORITY, token_cache=cache)

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        # ここでブラウザが自動的に開き、Microsoftアカウントへのログインを求める
        result = app.acquire_token_interactive(scopes=SCOPES)

    _save_token_cache(cache)

    if not result or "access_token" not in result:
        error_desc = (result or {}).get("error_description", "不明なエラー")
        raise RuntimeError(f"Outlookへのログインに失敗しました: {error_desc}")

    return result["access_token"]


def get_busy_events(target_date):
    """
    指定日のOutlook予定を取得する【本物のMicrosoft Graph連携】。

    戻り値: [{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]
    google_calendar_service.get_busy_events() と同じ形式。
    """
    token = _get_access_token()

    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)

    headers = {
        "Authorization": f"Bearer {token}",
        # 日本時間で予定の開始・終了を受け取る
        "Prefer": 'outlook.timezone="Tokyo Standard Time"',
    }
    params = {
        "startDateTime": start_dt.isoformat(),
        "endDateTime": end_dt.isoformat(),
        "$orderby": "start/dateTime",
        "$select": "subject,start,end,isAllDay",
    }

    resp = requests.get(
        f"{GRAPH_ENDPOINT}/me/calendarview",
        headers=headers,
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("value", [])

    events = []
    for item in items:
        if item.get("isAllDay"):
            # 終日予定（祝日・休暇など）はその日の空き時間計算から除外する
            continue
        # Graph APIの dateTime は "2026-09-22T09:00:00.0000000" のような形式で
        # 返るので、"HH:MM" 部分だけを取り出す
        start_str = item["start"]["dateTime"][11:16]
        end_str = item["end"]["dateTime"][11:16]
        events.append(
            {
                "start": start_str,
                "end": end_str,
                "summary": item.get("subject") or "(無題の予定)",
            }
        )
    return events
