"""
「ホーム」画面。

新着の支援依頼と、直近登録した余白時間に基づくおすすめを表示する。
"""

from datetime import date

import streamlit as st

import free_time_repository
import matching
import request_repository
import sidebar


def render(employee):
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

    b1, b2 = st.columns(2)
    with b1:
        st.info("🕐 **空いている時間を登録**\n\n日時・時間・スキルを登録すると、あなたに合う候補を探します。")
        if st.button("余白時間を登録する", type="primary", use_container_width=True):
            sidebar.navigate_to("余白時間を登録")
            st.rerun()

    with b2:
        st.success("🔍 **支援を探す**\n\n他部署の支援依頼から、あなたのスキルに合う仕事を探します。")
        if st.button("支援を探す", use_container_width=True):
            sidebar.navigate_to("支援を探す")
            st.rerun()

    st.write("")
    st.subheader("🆕 新着の支援依頼")
    requests_df = request_repository.get_requests()
    if requests_df.empty:
        st.info("現在、支援依頼はありません。")
    else:
        display_df = requests_df.head(5).copy()
        display_df["希望日時"] = display_df["request_date"] + " " + display_df["start_time"] + "～" + display_df["end_time"]
        display_df["必要スキル"] = display_df["skills"]
        display_df = display_df[
            ["department", "title", "希望日時", "required_hours", "people_needed", "必要スキル"]
        ]
        display_df.columns = ["部署", "業務内容", "希望日時", "所要時間(h)", "人数", "必要スキル"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

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
    else:
        st.info("まだ余白時間が登録されていません。")
