"""
「支援を依頼する」画面。

忙しい部署が他部署への支援依頼を新規登録するフォーム。
"""

from datetime import date, time, timedelta

import streamlit as st

import request_repository
from config import SKILL_OPTIONS


def render(employee):
    st.header("➕ 支援を依頼する")
    st.write("忙しい部署から、他部署へ支援してほしい業務を登録します。")

    with st.form("request_form"):
        c1, c2 = st.columns(2)
        with c1:
            department = st.text_input("部署", value=employee["department"])
            title = st.text_input("業務名", placeholder="例：営業部のデータチェック")
            request_date = st.date_input("希望日", value=date.today() + timedelta(days=1))
        with c2:
            start = st.time_input("開始時刻", value=time(13, 0), step=timedelta(minutes=30))
            end = st.time_input("終了時刻", value=time(17, 0), step=timedelta(minutes=30))
            people = st.number_input("必要人数", min_value=1, max_value=20, value=1)

        description = st.text_area("業務内容", placeholder="どのような作業を手伝ってほしいか")
        required_hours = st.number_input("想定所要時間（時間）", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
        skills = st.multiselect("必要スキル", SKILL_OPTIONS)

        submitted = st.form_submit_button("支援依頼を登録", type="primary", use_container_width=True)

        if submitted:
            if not title:
                st.error("業務名を入力してください。")
            elif end <= start:
                st.error("終了時刻は開始時刻より後にしてください。")
            else:
                request_repository.insert_request(
                    department=department,
                    title=title,
                    description=description,
                    request_date=request_date.isoformat(),
                    start_time=start.strftime("%H:%M"),
                    end_time=end.strftime("%H:%M"),
                    required_hours=required_hours,
                    people_needed=people,
                    skills=",".join(skills),
                )
                st.success("支援依頼を登録しました。")
