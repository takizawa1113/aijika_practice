"""
「マイページ」画面。

ログイン中社員のプロフィールと、登録済み余白時間の一覧を表示する。
"""

import streamlit as st

import employee_repository
import free_time_repository
from config import SKILL_OPTIONS

@st.dialog("削除確認")
def confirm_delete(id):
    st.write("本当に削除しますか？")

    if st.button("はい"):
        free_time_repository.delete_free_time(id)
        st.rerun()

    if st.button("キャンセル"):
        st.rerun()

def render(employee):
    # ============================================================
    # 編集モードの初期化
    # ============================================================
    if "mypage_edit_mode" not in st.session_state:
        st.session_state.mypage_edit_mode = False

    # ============================================================
    # ヘッダー
    # ============================================================
    c1, c2, c3 = st.columns([5, 1, 1])

    with c1:
        st.header("👤 マイページ")

    with c2:
        if st.button(
            "修正",
            disabled=st.session_state.mypage_edit_mode,
            use_container_width=True,
        ):
            st.session_state.mypage_edit_mode = True
            st.rerun()

    with c3:
        if st.button(
            "再登録",
            disabled=not st.session_state.mypage_edit_mode,
            type="primary",
            use_container_width=True,
        ):
            # 入力値を取得
            name = st.session_state.mypage_name.strip()
            department = st.session_state.mypage_department.strip()
            skills = st.session_state.mypage_skills

            # 名前チェック
            if not name:
                st.error("名前を入力してください。")

            # 所属部署チェック
            elif not department:
                st.error("所属部署を入力してください。")

            else:
                # DBを更新
                employee_repository.update_employee(
                    employee_id=employee["id"],
                    name=name,
                    department=department,
                    skills=",".join(skills),
                )

                st.session_state.mypage_edit_mode = False

                st.success("登録内容を更新しました。")
                st.rerun()

    # ============================================================
    # プロフィール
    # ============================================================
    if st.session_state.mypage_edit_mode:

        # 編集モード
        c1, c2, c3 = st.columns(3)

        with c1:
            st.text_input(
                "名前",
                value=employee["name"],
                key="mypage_name",
            )

        with c2:
            st.text_input(
                "所属部署",
                value=employee["department"],
                key="mypage_department",
            )

        with c3:
            # 登録スキル数は選択中のスキル数を表示
            skill_count = len(
                st.session_state.get(
                    "mypage_skills",
                    employee["skills"],
                )
            )

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-number">{skill_count}</div>
                    <div class="metric-label">登録スキル数</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        # 通常モード
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-number">{employee["name"]}</div>'
                f'<div class="metric-label">社員</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-number">{employee["department"]}</div>'
                f'<div class="metric-label">所属部署</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-number">{len(employee["skills"])}</div>'
                f'<div class="metric-label">登録スキル数</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ============================================================
    # 登録スキル
    # ============================================================
    st.write("")
    st.subheader("登録スキル")

    if st.session_state.mypage_edit_mode:

        # 編集モード
        st.multiselect(
            "登録するスキル",
            SKILL_OPTIONS,
            default=employee["skills"],
            key="mypage_skills",
        )

    else:

        # 通常モード
        if employee["skills"]:
            st.write(
                "　".join(
                    [f"🏷️ {s}" for s in employee["skills"]]
                )
            )
        else:
            st.caption("登録スキルはありません。")

    # ============================================================
    # 登録した余白時間
    # ============================================================
    st.subheader("登録した余白時間")

    free_df = free_time_repository.get_free_times(employee["id"])

    if free_df.empty:
        st.info("登録はありません。")

    else:
        view = free_df[
            [
                "id",
                "free_date",
                "start_time",
                "end_time",
                "skills",
                "preference",
            ]
        ].copy()

        # ヘッダー
        b1, b2, b3, b4, b5, b6 = st.columns(6)

        with b1:
            st.markdown("**日付**")

        with b2:
            st.markdown("**開始**")

        with b3:
            st.markdown("**終了**")

        with b4:
            st.markdown("**スキル**")

        with b5:
            st.markdown("**希望**")

        with b6:
            st.markdown("**操作**")

        # データ
        for _, b in view.iterrows():
            b1, b2, b3, b4, b5, b6 = st.columns(6)

            with b1:
                st.write(b["free_date"])

            with b2:
                st.write(b["start_time"])

            with b3:
                st.write(b["end_time"])

            with b4:
                st.write(b["skills"])

            with b5:
                st.write(b["preference"])

            with b6:
                if st.button("削除", key=b["id"]):
                    confirm_delete(b["id"])