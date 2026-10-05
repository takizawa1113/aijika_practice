"""
サイドバー（メニュー・ログイン情報表示）を担当するモジュール。

ページの追加・並び替えは config.PAGES を編集するだけでよい。
"""

import streamlit as st

from config import APP_TAGLINE, LOGO_PATH, PAGES


def navigate_to(page_name):
    """
    他の画面（例: ホームのボタン）からメニューを切り替えたいときに呼ぶ。

    Streamlitの制約上、ラジオウィジェット（key="menu_radio"）の値は
    それが描画された後の同じ実行内では変更できない。そのため実際の
    切り替えは「予約」だけ行い、次の再実行時に render_sidebar() が
    ウィジェット描画前に反映する。呼び出し側は続けて st.rerun() する。
    """
    st.session_state["nav_target"] = page_name


def render_sidebar(employee):
    labels = [f"{icon} {name}" for icon, name in PAGES]
    names = [name for _, name in PAGES]

    # navigate_to() による遷移予約があれば、ウィジェット生成前に反映する。
    pending = st.session_state.pop("nav_target", None)
    if pending in names:
        st.session_state["menu_radio"] = labels[names.index(pending)]
    elif "menu_radio" not in st.session_state:
        # ブラウザの再読み込みでsession_stateが失われても、
        # URLのクエリパラメータ（?page=...）から直前の画面を復元する。
        default_name = st.session_state.get(
            "selected_page",
            st.query_params.get("page", names[0]),
        )
        default_index = names.index(default_name) if default_name in names else 0
        st.session_state["menu_radio"] = labels[default_index]

    with st.sidebar:
        st.image(LOGO_PATH, width=160)
        st.caption(APP_TAGLINE)
        st.divider()

        choice = st.radio(
            "メニュー",
            labels,
            label_visibility="collapsed",
            key="menu_radio",
        )
        page = names[labels.index(choice)]
        st.session_state.selected_page = page
        st.query_params["page"] = page

        st.divider()
        st.caption(f"ログイン中：{employee['name']}")
        st.caption(f"{employee['department']} / {employee['role']}")
        st.caption("MVP v0.1")

    return page
