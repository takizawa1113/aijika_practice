"""
「休暇のおすすめ」UI部品。

calendar_widget.py と同じく、画面側（views/free_time_form.py, views/home.py）
からは関数を1行呼ぶだけで使えるようにしてある。
ロジックは vacation_recommender.py、データは vacation_dummy_data.py に分離。
"""

from datetime import date, datetime, timedelta

import streamlit as st

import vacation_dummy_data as data
import vacation_recommender as rec


def _metric(col, number, label):
    col.markdown(
        f'<div class="metric-card"><div class="metric-number">{number}</div>'
        f'<div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def _build_ics(free_date, start, end, leave_type):
    """休暇予定を .ics（Outlook / Googleカレンダーに取り込める形式）で作る。"""
    try:
        from icalendar import Calendar, Event
    except ImportError:
        return None
    cal = Calendar()
    cal.add("prodid", "-//akijikan//vacation//JP")
    cal.add("version", "2.0")
    ev = Event()
    ev.add("summary", f"🌴 {leave_type}")
    if leave_type == "全休":
        ev.add("dtstart", free_date)
    else:
        ev.add("dtstart", datetime.combine(free_date, start))
        ev.add("dtend", datetime.combine(free_date, end))
    ev.add("uid", f"vacation-{free_date.isoformat()}-{start.strftime('%H%M')}@akijikan")
    cal.add_component(ev)
    return cal.to_ical()


def render_vacation_suggestions(employee, free_date, start, end, preferences, requests_df):
    """
    マッチする支援依頼が無かったときに表示する「休暇のおすすめ」一式。
    start / end は datetime.time。
    """
    holidays = data.get_holidays()
    team_plans = data.get_team_leave_plans()
    balance = data.get_leave_balance(employee["id"])

    leave = rec.classify_leave(start, end)
    long_weekend = rec.long_weekend_info(free_date, leave, holidays)
    obligation = rec.leave_obligation_status(balance, date.today())
    conflicts = rec.team_conflicts(employee["department"], free_date, team_plans)

    st.subheader("🌴 休暇のおすすめ")
    st.caption("※ 有給残・チームの休暇予定・祝日はデモ用のダミーデータです。")

    # --- サマリー ---
    c1, c2, c3 = st.columns(3)
    _metric(c1, leave["type"].split("（")[0], f"{rec.fmt_date(free_date)} のおすすめ")
    _metric(c2, long_weekend["label"].split("（")[0] or "―", "連休になる？")
    _metric(c3, f"{balance['remaining']:g}日", f"有給の残り（消化 {leave['days']:g}日）")

    st.write("")
    if long_weekend["days"]:
        st.success(f"🎌 {leave['type']}にすると **{long_weekend['label']}** になります！")
    if conflicts:
        names = "、".join(f"{p['name']}さん（{p['type']}）" for p in conflicts)
        st.warning(f"⚠️ この日は{employee['department']}で {names} が休み予定です。下の候補日も検討してください。")
    else:
        st.info(f"✅ この日は{employee['department']}の休みと重なっていません。")

    if obligation["shortfall"] > 0:
        st.warning(f"📌 {obligation['message']}")
    else:
        st.caption(f"📌 {obligation['message']}")

    # --- 休みやすい日ランキング ---
    with st.expander("📆 もっと休みやすい日は？（今後2週間）", expanded=bool(conflicts)):
        base_type = leave["type"] if leave["type"] in ("全休", "午前半休", "午後半休") else "全休"
        for i, c in enumerate(rec.rank_leave_days(employee["department"], date.today() + timedelta(days=1), team_plans, holidays, base_type), 1):
            st.markdown(f"**{i}. {rec.fmt_date(c['date'])} に{base_type}**　" + "　".join(c["reasons"]))

    # --- 過ごし方 ---
    st.markdown("#### 💡 こんな過ごし方はどう？")
    gap = rec.skill_demand_gap(employee["skills"], requests_df)
    activities = rec.recommend_activities(leave["hours"], preferences, gap, data.get_activity_catalog())
    cols = st.columns(len(activities))
    for col, (cat, items) in zip(cols, activities.items()):
        with col:
            st.markdown(f"**{cat}**")
            for a in items:
                note = f'<br><span class="small-note">⭐ {a["note"]}</span>' if a.get("note") else ""
                st.markdown(
                    f'<div class="recommend">{a["icon"]} {a["title"]}{note}</div>',
                    unsafe_allow_html=True,
                )

    # --- 次のアクション ---
    st.markdown("#### ✉️ そのまま申請する")
    a1, a2 = st.columns([3, 1])
    with a1:
        st.text_area(
            "上長への休暇申請（コピーして使えます）",
            rec.build_leave_request_text(employee, free_date, start, end, leave),
            height=120,
            key="vacation_request_text",
        )
    with a2:
        st.write("")
        ics = _build_ics(free_date, start, end, leave["type"].split("（")[0])
        if ics:
            st.download_button(
                "📅 カレンダーに追加（.ics）",
                ics,
                file_name=f"vacation_{free_date.isoformat()}.ics",
                mime="text/calendar",
                use_container_width=True,
            )


def render_compact(employee, free_date, start, end):
    """ホーム画面向けの1行サマリー版。"""
    leave = rec.classify_leave(start, end)
    lw = rec.long_weekend_info(free_date, leave, data.get_holidays())
    obligation = rec.leave_obligation_status(data.get_leave_balance(employee["id"]), date.today())
    msg = f"🌴 {rec.fmt_date(free_date)} は **{leave['type']}** がおすすめです"
    if lw["days"]:
        msg += f" → {lw['label']}"
    msg += "。"
    if obligation["shortfall"] > 0:
        msg += f"\n\n📌 {obligation['message']}"
    st.info(msg)
