"""
「マイページ」画面。

ログイン中社員のプロフィールと、登録済み余白時間の一覧を表示する。
"""

import streamlit as st

import free_time_repository


def render(employee):
    st.header("👤 マイページ")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{employee["name"]}</div>'
            f'<div class="metric-label">社員</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{employee["department"]}</div>'
            f'<div class="metric-label">所属部署</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{len(employee["skills"])}</div>'
            f'<div class="metric-label">登録スキル数</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("登録スキル")
    st.write("　".join([f"🏷️ {s}" for s in employee["skills"]]))

    st.subheader("登録した余白時間")
    free_df = free_time_repository.get_free_times(employee["id"])
    if free_df.empty:
        st.info("登録はありません。")
    else:
        view = free_df[["free_date", "start_time", "end_time", "skills", "preference"]].copy()
        view.columns = ["日付", "開始", "終了", "スキル", "希望"]
        st.dataframe(view, use_container_width=True, hide_index=True)
