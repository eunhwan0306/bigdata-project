import streamlit as st

st.set_page_config(
    page_title="고속도로 돌발상황 위험도 예측",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

eda   = st.Page("pages/1_EDA.py",      title="데이터 탐색 (EDA)",    icon="📊", default=True)
viz   = st.Page("pages/2_시각화.py",   title="시각화",                icon="📈")
model = st.Page("pages/3_모델_서비스.py", title="위험도 예측 서비스", icon="🔮")

pg = st.navigation({"고속도로 위험도 분석": [eda, viz, model]})

st.sidebar.markdown("### 🚗 고속도로 돌발상황 예측")
st.sidebar.caption("실시간 연쇄 정체 위험도 진단 시스템")
st.sidebar.markdown("---")
st.sidebar.info(
    "**데이터 출처**\n"
    "- 국토교통부 돌발상황 API\n"
    "- 한국도로공사 교통사고 CSV\n"
    "- 기상청 ASOS 시간별 자료"
)
st.sidebar.markdown("---")
st.sidebar.caption("빅데이터분析프로그래밍 기말과제 | 20221652 주은환")

pg.run()
