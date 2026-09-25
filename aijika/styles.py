"""
アプリ共通のCSS定義。

デザインを調整する担当者はこのファイルだけを触れば良く、
他の機能ファイルとコンフリクトしない。
"""

import streamlit as st

CUSTOM_CSS = """
<style>
.main-title {
    font-size: 2.1rem;
    font-weight: 700;
    color: #17365d;
    margin-bottom: 0.2rem;
}
.sub-title {
    color: #5d6b7a;
    font-size: 1rem;
    margin-bottom: 1.2rem;
}
.hero {
    background: linear-gradient(135deg, #eaf5ff 0%, #f5fbff 100%);
    border-radius: 16px;
    padding: 2rem 2.3rem;
    margin-bottom: 1.2rem;
    border: 1px solid #dceeff;
}
.hero h1 {
    color: #17365d;
    font-size: 2.6rem;
    margin: 0;
}
.hero p {
    color: #40566e;
    font-size: 1.1rem;
}
.section-card {
    border: 1px solid #e3eaf1;
    border-radius: 14px;
    padding: 1.1rem;
    background: white;
}
.metric-card {
    border-radius: 14px;
    padding: 1rem;
    border: 1px solid #e1e8ef;
    background: #ffffff;
    text-align: center;
}
.metric-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1976d2;
}
.metric-label {
    color: #667788;
    font-size: 0.9rem;
}
.recommend {
    border-left: 5px solid #1976d2;
    background: #f6fbff;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.7rem;
}
.score {
    color: #1976d2;
    font-weight: 700;
    font-size: 1.05rem;
}
.small-note {
    color: #758494;
    font-size: 0.82rem;
}
div[data-testid="stSidebar"] {
    border-right: 1px solid #e5e9ef;
}
</style>
"""


def apply_styles():
    """アプリ共通CSSを適用する。app.py の先頭で一度だけ呼び出す。"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
