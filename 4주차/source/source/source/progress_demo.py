import streamlit as st
import time

st.title('진행 표시 바')

if st.button('작업 시작'):
    bar = st.progress(0)
    for i in range(100):
        bar.progress(i + 1)
        time.sleep(0.01)
    st.success('완료!')

import streamlit as st
import time

status = st.empty()
bar = st.progress(0)

status.write('⏳ 데이터 로딩 중...')
for i in range(100):
    bar.progress(i + 1)
    time.sleep(0.02)

bar.empty()
status.write('✅ 로딩 완료!') 

import streamlit as st
import time

with st.spinner('데이터를 분석하는 중...'):
    time.sleep(3) # 시간이 걸리는 작업
st.success('분석 완료!')

import streamlit as st

st.toast('저장되었습니다!')

st.balloons()
st.snow()