"""
Googleカレンダー連携モジュール（現在はダミーデータ版）。

【今の状態】
本物のGoogle Calendar APIはまだ呼んでいない。デモ・発表用に、
「その日の予定を読み込んで空き時間を計算する」という一連の流れを
ダミーデータで再現している。

【本物のAPIに差し替えるときにやること】
差し替えが必要なのは `get_busy_events()` の中身だけでよい。
他のファイル（views/free_time_form.py, compute_free_slots()）は
「[{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...] という
形のリストが返ってくる」という前提でしか作っていないため、
戻り値の形式さえ揃えれば呼び出し側は一切変更不要。

本番実装の大まかな流れ（参考）:
    1. Google Cloud Consoleでプロジェクトを作成し、Calendar APIを有効化
    2. OAuthクライアントID（デスクトップアプリ種別）を発行し、
       credentials.json をこのプロジェクト直下に置く
    3. requirements.txt に以下を追加してインストール:
       google-auth, google-auth-oauthlib, google-api-python-client
    4. 初回はブラウザでGoogleログイン（InstalledAppFlow.run_local_server()）、
       token.json をキャッシュして次回以降は自動認証
    5. `service.events().list(calendarId="primary", timeMin=..., timeMax=...)`
       などで指定日の予定を取得し、下記と同じ形式のリストに整形して返す

    ※ローカル実行（発表者のPCで streamlit run）であればOAuthのローカルサーバー
      方式がそのまま使えるが、Streamlit Community Cloud等にデプロイする場合は
      リダイレクトURIの設定が別途必要になる点に注意。
"""

import random

import calendar_utils
from config import MIN_FREE_SLOT_MINUTES, WORK_END_TIME, WORK_START_TIME

# ダミーの「予定」候補（本番ではGoogle Calendar APIのレスポンスに相当する）
_DUMMY_EVENT_POOL = [
    ("09:00", "10:00", "朝会"),
    ("10:30", "12:00", "定例MTG"),
    ("13:00", "14:00", "資料レビュー"),
    ("14:30", "15:00", "電話対応"),
    ("15:30", "16:30", "部内共有"),
    ("16:30", "17:00", "1on1"),
]


def get_busy_events(target_date):
    """
    指定日のカレンダー予定（busy時間帯）を返す【現在はダミーデータ】。

    戻り値: [{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]

    日付をシードにして乱数を固定しているので、同じ日を指定すれば
    デモ中は何度確認しても同じ予定が表示される。
    """
    rng = random.Random(target_date.isoformat())
    n = rng.randint(2, 4)
    chosen = rng.sample(_DUMMY_EVENT_POOL, n)
    events = [
        {"start": s, "end": e, "summary": title}
        for s, e, title in sorted(chosen)
    ]
    return events


def compute_free_slots(target_date, work_start=WORK_START_TIME, work_end=WORK_END_TIME, min_slot_minutes=MIN_FREE_SLOT_MINUTES):
    """
    勤務時間帯からカレンダーの予定を差し引いて、空き時間帯の候補を返す。

    戻り値: [(start_time, end_time), ...]（datetime.time のタプルのリスト）
    実際の計算は calendar_utils（Outlook版とも共通）に委譲している。
    """
    events = get_busy_events(target_date)
    return calendar_utils.compute_free_slots_from_events(
        events, work_start=work_start, work_end=work_end, min_slot_minutes=min_slot_minutes
    )
