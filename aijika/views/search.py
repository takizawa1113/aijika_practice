"""
「支援を探す」画面。

他部署の支援依頼を日付・スキル・部署で絞り込んで一覧表示する。
"""

from datetime import datetime

import streamlit as st

import request_repository
from config import SKILL_OPTIONS


@st.dialog("支援依頼を修正")
def edit_request_dialog(r, employee_id):
    current_skills = [
        skill.strip()
        for skill in str(r["skills"]).split(",")
        if skill.strip()
    ]

    with st.form("edit_request_form"):
        department = st.text_input(
            "部署",
            value=r["department"],
        )

        title = st.text_input(
            "業務名",
            value=r["title"],
        )

        description = st.text_area(
            "業務内容",
            value=r["description"],
        )

        request_date = st.date_input(
            "希望日",
            value=datetime.strptime(
                r["request_date"], "%Y-%m-%d"
            ).date(),
        )

        col1, col2 = st.columns(2)

        with col1:
            start = st.time_input(
                "開始時刻",
                value=datetime.strptime(
                    r["start_time"], "%H:%M"
                ).time(),
            )

        with col2:
            end = st.time_input(
                "終了時刻",
                value=datetime.strptime(
                    r["end_time"], "%H:%M"
                ).time(),
            )

        people = st.number_input(
            "必要人数",
            min_value=1,
            max_value=20,
            value=int(r["people_needed"]),
        )

        required_hours = st.number_input(
            "想定所要時間（時間）",
            min_value=0.5,
            max_value=8.0,
            value=float(r["required_hours"]),
            step=0.5,
        )

        skills = st.multiselect(
            "必要スキル",
            SKILL_OPTIONS,
            default=[
                skill
                for skill in current_skills
                if skill in SKILL_OPTIONS
            ],
        )

        submitted = st.form_submit_button(
            "変更を保存",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not title:
                st.error("業務名を入力してください。")
                return

            if end <= start:
                st.error("終了時刻は開始時刻より後にしてください。")
                return

            updated = request_repository.update_request(
                request_id=int(r["id"]),
                employee_id=employee_id,
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

            if updated:
                st.session_state["request_update_message"] = "支援依頼を変更しました。"
                st.rerun()
            else:
                st.error("修正できませんでした。")


@st.dialog("支援依頼を削除")
def delete_request_dialog(request_id, employee_id):
    st.write("この支援依頼を削除しますか？")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "キャンセル",
            use_container_width=True,
        ):
            st.rerun()

    with col2:
        if st.button(
            "削除",
            type="primary",
            use_container_width=True,
        ):
            deleted = request_repository.delete_request(
                request_id=request_id,
                employee_id=employee_id,
            )

            if deleted:
                st.session_state["request_delete_message"] = (
                    "支援依頼を削除しました。"
                )
                st.rerun()
            else:
                st.error("削除できませんでした。")


def clear_focus():
    st.session_state.pop("focus_request_id", None)


def toggle_detail(detail_key):
    st.session_state[detail_key] = not st.session_state.get(detail_key, False)


def render(employee):
    st.header("🔍 支援を探す")

    if "request_update_message" in st.session_state:
        st.success(st.session_state.pop("request_update_message"))

    if "request_delete_message" in st.session_state:
        st.success(st.session_state.pop("request_delete_message"))

    mode = st.radio(
        "表示",
        ["支援を探す", "自分が登録した支援"],
        horizontal=True,
        on_change=clear_focus,
    )

    if mode == "支援を探す":
        st.write("他部署の支援依頼から、自分に合う仕事を探します。")
        df = request_repository.get_requests()
    else:
        st.write("自分が登録した支援依頼を確認・修正・削除します。")
        df = request_repository.get_my_requests(employee["id"])


    # ホームの「詳細」ボタンから来た場合、その案件の詳細を自動で開く。
    if "jump_to_request_id" in st.session_state:
        jump_id = st.session_state.pop("jump_to_request_id")
        for key in [k for k in st.session_state if k.startswith("show_request_")]:
            st.session_state[key] = False
        st.session_state["focus_request_id"] = jump_id
        st.session_state[f"show_request_{jump_id}"] = True
    focus_id = st.session_state.get("focus_request_id")

    c1, c2, c3 = st.columns(3)
    with c1:
        target_date = st.date_input(
            "希望日（未指定で全期間から検索）", value=None, on_change=clear_focus
        )
    with c2:
        skill_filter = st.text_input(
            "スキルで絞り込み", placeholder="例：Excel", on_change=clear_focus
        )
    with c3:
        dept_filter = st.selectbox(
            "部署",
            ["すべて"] + sorted(df["department"].unique().tolist()),
            on_change=clear_focus,
        )

    filtered = df[df["status"] == "募集中"].copy()
    if target_date:
        filtered = filtered[filtered["request_date"] == target_date.isoformat()]

    if dept_filter != "すべて":
        filtered = filtered[filtered["department"] == dept_filter]

    if skill_filter:
        filtered = filtered[
            filtered["skills"].str.contains(skill_filter, case=False, na=False)
        ]

    # ホームから選んだ案件は、全件の中で一番上に表示する。
    if focus_id is not None and focus_id in filtered["id"].values:
        filtered = filtered.assign(_focus=filtered["id"] == focus_id).sort_values(
            "_focus", ascending=False, kind="stable"
        )

    if filtered.empty:
        st.warning("条件に一致する支援依頼はありません。")
    else:
        for _, r in filtered.iterrows():
            if focus_id is not None and r["id"] == focus_id:
                st.markdown("📌 **ホームで選んだ支援依頼**")
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
                    detail_key = f"show_request_{r['id']}"
                    is_open = st.session_state.get(detail_key, False)
                    st.button(
                        "詳細を隠す" if is_open else "詳細を見る",
                        key=f"detail_{r['id']}",
                        use_container_width=True,
                        on_click=toggle_detail,
                        args=(detail_key,),
                    )


                    if mode == "自分が登録した支援":
                        if st.button(
                            "修正",
                            key=f"edit_{r['id']}",
                            use_container_width=True
                        ):
                            edit_request_dialog(r, employee["id"])

                        if st.button(
                            "削除",
                            key=f"delete_{r['id']}",
                            use_container_width=True
                        ):
                            delete_request_dialog(
                                int(r["id"]),
                                employee["id"],
                            )



            if st.session_state.get(f"show_request_{r['id']}", False):
                st.info(
                    f"**業務詳細**\n\n{r['description']}\n\n"
                    f"必要スキル：{r['skills']}\n\n"
                    f"所要時間：約{r['required_hours']}時間"
                )
