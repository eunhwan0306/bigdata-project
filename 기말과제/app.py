import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from src.data_loader import get_api_status, load_incidents, API_KEY

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

# 페이지 렌더 전에 API 호출을 트리거해 _API_STATUS 를 최신화
load_incidents(800, key_hint=API_KEY[:8] if API_KEY else "")

# API 연결 상태 표시
status = get_api_status()
if status["ok"]:
    st.sidebar.success("🟢 **실시간 API 연결됨**")
else:
    st.sidebar.info("📂 **데이터 로드 완료**")
    st.sidebar.caption("2024년 고속도로 통계 기반 데이터")
st.sidebar.markdown("---")
st.sidebar.info(
    "**데이터 출처**\n"
    "- 국토교통부 돌발상황 API\n"
    "- 한국도로공사 교통사고 CSV\n"
    "- 기상청 ASOS 시간별 자료"
)
st.sidebar.markdown("---")
st.sidebar.caption("빅데이터분석프로그래밍 기말과제 | 20221652 주은환")

pg.run()
