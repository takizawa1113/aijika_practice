"""
アプリのエントリーポイント。

このファイルは「初期化」と「どの画面を出すか」のルーティングだけを行い、
各画面の中身は views/ 配下の各ファイルに委譲する。
機能追加・修正のほとんどは views/ 配下や *_repository.py を触ればよく、
このファイルを編集する頻度は最小限になるようにしてある。
"""

import streamlit as st

import config
import database
import employee_repository
import sidebar
import styles
from views import calendar_view, free_time_form, home, mypage, notices, request_form, search

# ============================================================
# 基本設定
# ============================================================
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state=config.INITIAL_SIDEBAR_STATE,
)

styles.apply_styles()
database.init_db()


# ============================================================
# セッション初期化
# ============================================================
if "employee_id" not in st.session_state:
    st.session_state.employee_id = 1

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "ホーム"

employee = employee_repository.get_employee(st.session_state.employee_id)


# ============================================================
# サイドバー・ヘッダー
# ============================================================
page = sidebar.render_sidebar(employee)

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(f'<div class="main-title">{config.APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{config.APP_TAGLINE}</div>', unsafe_allow_html=True)
with col2:
    st.write("")
    st.button("ログアウト", disabled=True, use_container_width=True)


# ============================================================
# 画面ディスパッチ
# 新しい画面を追加する場合は views/ にファイルを追加し、
# ここと config.PAGES に1行ずつ足すだけでよい。
# ============================================================
PAGE_RENDERERS = {
    "ホーム": home.render,
    "支援を探す": search.render,
    "支援を依頼する": request_form.render,
    "余白時間を登録": free_time_form.render,
    "カレンダー": calendar_view.render,
    "マイページ": mypage.render,
    "お知らせ": notices.render,
}

render_page = PAGE_RENDERERS.get(page, home.render)
render_page(employee)


# ============================================================
# Footer
# ============================================================
st.divider()
st.caption(f"{config.APP_NAME} {config.APP_TAGLINE} / MVP v0.1")
