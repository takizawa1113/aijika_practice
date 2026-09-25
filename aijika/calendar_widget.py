"""
「余白時間を登録」画面向けの、カレンダー連携UI部品。

このファイルは calendar_utils.py / google_calendar_service.py /
outlook_calendar_service.py とあわせて「カレンダー連携機能一式」として
独立させてある（担当: Aさん想定）。

views/free_time_form.py（担当: Cさん想定）からは、この
render_suggestions() を1行呼び出すだけで使える。カレンダー連携の
改修（連携先の追加、UIの調整など）はすべてこのファイルの中で完結し、
Cさんが同時に views/free_time_form.py の別の場所（フォーム項目や
マッチング結果表示など）を編集していても、コンフリクトがほぼ起きない
構成にしている。
"""

from datetime import date, timedelta

import streamlit as st

import calendar_utils
import google_calendar_service
import outlook_calendar_service
import outlook_ics_calendar_service

# 連携先の切り替え。デモ本番でOutlook連携がうまく繋がらない場合に備えて、
# その場で「ダミーデータ」に切り替えられるようにしてある（安全弁）。
#
# - ダミーデータ: 常に動く。ネット・ログイン一切不要。
# - Outlook（ICS・かんたん版）: Azure Portでのアプリ登録が不要。
#   「カレンダーを公開」機能のURL、または.icsファイルのアップロードで、
#   本物の予定を表示できる。詳しくは outlook_ics_calendar_service.py 参照。
# - Outlook（本物・Microsoft Graph）: Azure Portalでのアプリ登録が必要な、
#   本格的なOAuth連携版。詳しくは outlook_calendar_service.py 参照。
_CALENDAR_BACKENDS = {
    "ダミーデータ（デモ用）": google_calendar_service,
    "Outlook（ICS・かんたん版）": outlook_ics_calendar_service,
    "Outlook（本物・Microsoft Graph）": outlook_calendar_service,
}


def render_suggestions():
    
    """
    カレンダー連携セクションを描画する。

    選んだ日の「予定」を取得して空き時間の候補をボタンで提示する。
    候補ボタンを押すと、余白時間登録フォーム（key="free_time_date" /
    "free_time_start" / "free_time_end"）に自動反映される。
    このキーの名前だけが views/free_time_form.py との「取り決め」になる。
    """
    st.subheader("📅 カレンダーから空き時間を確認")

    backend_label = st.radio(
        "連携先",
        list(_CALENDAR_BACKENDS.keys()),
        horizontal=True,
        key="calendar_backend",
    )
    backend = _CALENDAR_BACKENDS[backend_label]

    if backend is google_calendar_service:
        st.caption("デモ用のダミーデータです。実際の予定ではありません。")
    elif backend is outlook_ics_calendar_service and not outlook_ics_calendar_service.uses_url():
        # 公開URLが未設定のときだけ、.icsファイルのアップロード欄を出す
        outlook_ics_calendar_service.render_upload_widget()

    cal_date = st.date_input(
        "確認する日",
        value=date.today() + timedelta(days=1),
        key="cal_check_date",
    )

    try:
        events = backend.get_busy_events(cal_date)
    except Exception as e:
        st.error(f"予定の取得に失敗しました：{e}")
        st.caption("うまくいかない場合は連携先を「ダミーデータ（デモ用）」に切り替えてください。")
        return

    if events:
        summary = " / ".join(f"{e['start']}～{e['end']} {e['summary']}" for e in events)
        st.caption(f"🗓 この日の予定：{summary}")
    else:
        st.caption("🗓 この日は登録されている予定がありません。")

    free_slots = calendar_utils.compute_free_slots_from_events(events)
    if not free_slots:
        st.info("この日は空き時間の候補が見つかりませんでした。")
        return

    st.write("空いている時間帯の候補（クリックで下のフォームに反映）：")
    cols = st.columns(len(free_slots))
    for col, (slot_start, slot_end) in zip(cols, free_slots):
        label = f"🕐 {slot_start.strftime('%H:%M')}～{slot_end.strftime('%H:%M')}"
        with col:
            if st.button(label, key=f"slot_{slot_start}_{slot_end}", use_container_width=True):
                st.session_state["free_time_date"] = cal_date
                st.session_state["free_time_start"] = slot_start
                st.session_state["free_time_end"] = slot_end
                st.rerun()
