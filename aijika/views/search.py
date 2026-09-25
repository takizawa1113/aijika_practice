"""
「支援を探す」画面。

他部署の支援依頼を日付・スキル・部署で絞り込んで一覧表示する。
"""

from datetime import date, timedelta

import streamlit as st

import request_repository


def render(employee):
    st.header("🔍 支援を探す")
    st.write("他部署の支援依頼から、自分に合う仕事を探します。")

    df = request_repository.get_requests()

    c1, c2, c3 = st.columns(3)
    with c1:
        target_date = st.date_input("希望日", value=date.today() + timedelta(days=1))
    with c2:
        skill_filter = st.text_input("スキルで絞り込み", placeholder="例：Excel")
    with c3:
        dept_filter = st.selectbox(
            "部署",
            ["すべて"] + sorted(df["department"].unique().tolist()),
        )

    filtered = df[df["status"] == "募集中"].copy()
    filtered = filtered[filtered["request_date"] == target_date.isoformat()]

    if dept_filter != "すべて":
        filtered = filtered[filtered["department"] == dept_filter]

    if skill_filter:
        filtered = filtered[
            filtered["skills"].str.contains(skill_filter, case=False, na=False)
        ]

    if filtered.empty:
        st.warning("条件に一致する支援依頼はありません。")
    else:
        for _, r in filtered.iterrows():
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.subheader(r["title"])
                    st.write(r["description"])
                    st.caption(
                        f"🏢 {r['department']}　"
                        f"📅 {r['request_date']}　"
                        f"🕐 {r['start_time']}～{r['end_time']}　"
                        f"👥 {r['people_needed']}名　"
                        f"🛠 {r['skills']}"
                    )
                with right:
                    if st.button("詳細を見る", key=f"detail_{r['id']}", use_container_width=True):
                        st.session_state[f"show_request_{r['id']}"] = True

            if st.session_state.get(f"show_request_{r['id']}", False):
                st.info(
                    f"**業務詳細**\n\n{r['description']}\n\n"
                    f"必要スキル：{r['skills']}\n\n"
                    f"所要時間：約{r['required_hours']}時間"
                )
