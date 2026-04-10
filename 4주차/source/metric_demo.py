import streamlit as st
st.title('KPI 대시보드')

st.metric(label="총 매출", value="₩1,250만", delta="15%")
st.metric(label="신규 고객", value="200명", delta="12명")
st.metric(label="이탈률", value="2.3%", delta="-0.5%", delta_color="inverse")

import streamlit as st

col1, col2, col3 = st.columns(3)
col1.metric("온도", "23°C", "1.5°C")
col2.metric("습도", "45%", "-2%")
col3.metric("풍속", "12km/h", "3km/h")

col1, col2 = st.columns(2)
with col1:
    st.write("왼쪽 영역")
with col2:
    st.write("오른쪽 영역")