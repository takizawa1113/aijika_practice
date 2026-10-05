"""
「ホーム」画面。

新着の支援依頼と、直近登録した余白時間に基づくおすすめを表示する。
"""

from datetime import date

import streamlit as st

import config
import free_time_repository
import matching
import request_repository
import sidebar
import vacation_widget


def render(employee):
    hero_text, hero_image = st.columns([4, 1], vertical_alignment="center")
    with hero_text:
        st.markdown(
            """
            <div class="hero">
                <h1>空いてる時間、どうする？</h1>
                <p>仕事を手伝う。休む。学ぶ。楽しむ。<br>
                あなたの余白に、最適な選択肢を。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_image:
        st.image(config.DEER_IMAGE_PATH, use_container_width=True)

    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "🕐 **空いている時間を登録**  \n日時・時間・スキルを登録すると、あなたに合う候補を探します。",
            type="primary",
            use_container_width=True,
            key="home_card_free_time",
        ):
            sidebar.navigate_to("余白時間を登録")
            st.rerun()

    with b2:
        if st.button(
            "🔍 **支援を探す**  \n他部署の支援依頼から、あなたのスキルに合う仕事を探します。",
            use_container_width=True,
            key="home_card_search",
        ):
            sidebar.navigate_to("支援を探す")
            st.rerun()

    st.write("")
    st.subheader("🆕 新着の支援依頼")

    requests_df = request_repository.get_requests()
    if requests_df.empty:
        st.info("現在、支援依頼はありません。")
    else:
        for _, r in requests_df.head(5).iterrows():
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**{r['title']}**　({r['department']})")
                    st.caption(
                        f"📅 {r['request_date']}　"
                        f"🕐 {r['start_time']}～{r['end_time']}　"
                        f"👥 {r['people_needed']}名　"
                        f"🛠 {r['skills']}"
                    )
                with right:
                    if st.button("詳細", key=f"home_detail_{r['id']}", use_container_width=True):
                        st.session_state["jump_to_request_id"] = r["id"]
                        sidebar.navigate_to("支援を探す")
                        st.rerun()

    st.subheader("💡 あなたへのおすすめ")
    st.caption("まず余白時間を登録すると、マッチングスコアを計算できます。")

    free_df = free_time_repository.get_free_times(employee["id"])
    if not free_df.empty:
        latest = free_df.iloc[-1]
        target_date = date.fromisoformat(latest["free_date"])
        recs = matching.make_recommendations(
            employee,
            target_date,
            latest["start_time"],
            latest["end_time"],
            requests_df,
        )
        if not recs.empty:
            for _, r in recs.head(4).iterrows():
                st.markdown(
                    f"""
                    <div class="recommend">
                        <strong>{r['title']}</strong>（{r['department']}）
                        <span class="score">マッチ度 {r['score']}%</span><br>
                        <span class="small-note">{r['reason']} / {r['start_time']}～{r['end_time']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("この余白時間に合う支援業務は見つかりませんでした。午後休・自己研鑽などの活用も検討できます。")
            vacation_widget.render_compact(
                employee,
                target_date,
                matching.parse_time(latest["start_time"]),
                matching.parse_time(latest["end_time"]),
            )
    else:
        st.info("まだ余白時間が登録されていません。")
