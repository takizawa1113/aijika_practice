"""
カレンダー連携で共通して使う「空き時間計算」ロジック。

google_calendar_service.py（ダミーデータ版）と outlook_calendar_service.py
（本物のMicrosoft Graph版）は、どちらも

    get_busy_events(date) -> [{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]

という同じ形式で予定を返す。取得元がダミーでもOutlookでも、
「予定の合間から勤務時間内の空き時間を計算する」ロジックは1つで
共通化しておく（データ取得元を増やしても、ここは変更不要にするため）。
"""

from datetime import datetime

from config import MIN_FREE_SLOT_MINUTES, WORK_END_TIME, WORK_START_TIME


def compute_free_slots_from_events(events, work_start=WORK_START_TIME, work_end=WORK_END_TIME, min_slot_minutes=MIN_FREE_SLOT_MINUTES):
    """
    予定リスト（busy時間帯）から、勤務時間内の空き時間帯を計算する。

    events: [{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]
    戻り値: [(start_time, end_time), ...]（datetime.time のタプルのリスト）
    min_slot_minutes 未満の細切れの空き時間は候補から除外する。
    """
    busy = []
    for ev in events:
        s = datetime.strptime(ev["start"], "%H:%M").time()
        e = datetime.strptime(ev["end"], "%H:%M").time()
        busy.append((s, e))
    busy.sort()

    free_slots = []
    cursor = work_start
    for s, e in busy:
        if s > cursor:
            free_slots.append((cursor, s))
        if e > cursor:
            cursor = max(cursor, e)
    if cursor < work_end:
        free_slots.append((cursor, work_end))

    def _minutes(t):
        return t.hour * 60 + t.minute

    return [
        (s, e) for s, e in free_slots
        if _minutes(e) - _minutes(s) >= min_slot_minutes
    ]
