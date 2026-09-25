"""
「カレンダー」画面。

登録済みの余白時間を月単位で一覧表示する。
"""

from datetime import date

import pandas as pd
import streamlit as st

import free_time_repository


def render(employee):
    st.header("📅 カレンダー")
    st.write("登録した余白時間を確認できます。")

    target_month = st.date_input("確認する日", value=date.today())
    free_df = free_time_repository.get_free_times(employee["id"])

    if free_df.empty:
        st.info("まだ余白時間は登録されていません。")
        return

    month_df = free_df[
        pd.to_datetime(free_df["free_date"]).dt.month == target_month.month
    ].copy()

    if month_df.empty:
        st.info("この月に登録された余白時間はありません。")
        return

    for _, r in month_df.iterrows():
        st.markdown(
            f"""
            <div class="recommend">
                <strong>🕐 {r['free_date']}</strong>
                {r['start_time']}～{r['end_time']}<br>
                スキル：{r['skills'] or '未設定'}<br>
                希望：{r['preference'] or '未設定'}
            </div>
            """,
            unsafe_allow_html=True,
        )
