"""
「余白時間を登録」画面。

社員が空いている日時・スキル・希望する過ごし方を登録し、
登録直後にマッチするおすすめ業務を表示する。
"""

from datetime import date, datetime, time, timedelta

import streamlit as st

import calendar_widget
import free_time_repository
import matching
import request_repository
from config import PREFERENCE_OPTIONS, SKILL_OPTIONS


def _init_default_free_time():
    """
    フォームの初期値をセットする。

    st.date_input / st.time_input に key を指定した状態で value も渡すと、
    「カレンダー候補ボタンで session_state を書き換えた後」に
    Streamlitから警告が出る（valueとsession_stateの二重管理になるため）。
    そのため、まだ値が無いときだけ session_state に初期値を入れておき、
    ウィジェット側には value を渡さない方式にしている。
    """
    if "free_time_date" not in st.session_state:
        st.session_state["free_time_date"] = date.today() + timedelta(days=1)
    if "free_time_start" not in st.session_state:
        st.session_state["free_time_start"] = time(13, 0)
    if "free_time_end" not in st.session_state:
        st.session_state["free_time_end"] = time(17, 0)


def render(employee):
    st.header("🕐 余白時間を登録")
    st.write("空いている日時・時間・スキルを登録してください。")

    calendar_widget.render_suggestions()
    st.divider()

    _init_default_free_time()

    with st.form("free_time_form"):
        free_date = st.date_input("空いている日", key="free_time_date")
        c1, c2 = st.columns(2)
        with c1:
            start = st.time_input("開始時刻", step=timedelta(minutes=30), key="free_time_start")
        with c2:
            end = st.time_input("終了時刻", step=timedelta(minutes=30), key="free_time_end")

        skills = st.multiselect(
            "活用できるスキル",
            SKILL_OPTIONS,
            default=employee["skills"][:2],
        )

        preference = st.multiselect(
            "希望する過ごし方",
            PREFERENCE_OPTIONS,
            default=["他部署支援"],
        )

        submitted = st.form_submit_button("登録する", type="primary", use_container_width=True)

    # 注意: st.button() は st.form() の中では使えない（st.form_submit_button のみ許可）ため、
    # フォーム送信後の表示・操作はフォームブロックの外側で行う。
    if submitted:
        if end <= start:
            st.error("終了時刻は開始時刻より後にしてください。")
        elif matching.hours_between(start, end) < 1:
            st.error("1時間以上の余白時間を登録してください。")
        else:
            free_time_repository.insert_free_time(
                employee_id=employee["id"],
                free_date=free_date.isoformat(),
                start_time=start.strftime("%H:%M"),
                end_time=end.strftime("%H:%M"),
                skills=",".join(skills),
                preference=",".join(preference),
                created_at=datetime.now().isoformat(timespec="seconds"),
            )

            st.success("余白時間を登録しました。下の「おすすめ」を確認してください。")

            requests_df = request_repository.get_requests()
            recs = matching.make_recommendations(
                employee,
                free_date,
                start.strftime("%H:%M"),
                end.strftime("%H:%M"),
                requests_df,
            )

            st.subheader("💡 この時間のおすすめ")
            if not recs.empty:
                for _, r in recs.head(5).iterrows():
                    st.markdown(
                        f"""
                        <div class="recommend">
                            <strong>{r['title']}</strong>（{r['department']}）
                            <span class="score">マッチ度 {r['score']}%</span><br>
                            {r['start_time']}～{r['end_time']} / {r['skills']}<br>
                            <span class="small-note">おすすめ理由：{r['reason']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button("応募画面へ"):
                    st.session_state.selected_free_date = free_date
                    st.info("MVPでは応募処理を実装できます。まずは対象業務を選択してください。")
            else:
                st.info(
                    "条件に合う支援業務は見つかりませんでした。\n\n"
                    "👉 午後休　👉 自己研鑽　👉 レジャー\n\n"
                    "など、別の余白活用方法を検討してみましょう。"
                )