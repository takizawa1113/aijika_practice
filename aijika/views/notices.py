"""
「お知らせ」画面。
"""

import streamlit as st

NOTICES = [
    ("お知らせ", "新機能「自己研鑽のおすすめ」を追加しました。"),
    ("ピックアップ", "経理部から新しい支援依頼が登録されました。"),
    ("メンテナンス", "システムメンテナンスのお知らせです。"),
]


def render(employee):
    st.header("🔔 お知らせ")

    for category, message in NOTICES:
        with st.container(border=True):
            st.caption(category)
            st.write(message)
