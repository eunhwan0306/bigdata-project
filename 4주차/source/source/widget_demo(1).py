import streamlit as st
import pandas as pd
import numpy as np

st.title('위젯 실습 - checkbox')

df = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)

st.line_chart(df)

if st.checkbox('원본 데이터 보기'):
    st.dataframe(df)

name = st.text_input('이름을 입력하세요', placeholder='홍길동')
st.write(f'입력된 이름: {name}')

feedback = st.text_area('의견을 작성해주세요', height=100)
st.write(f'입력 내용: {feedback}')

age = st.number_input('나이', min_value=0, max_value=150, value=25, step=1)
st.write(f'입력한 나이: {age}')

import datetime

date = st.date_input('날짜를 선택하세요', datetime.date.today())
st.write(f'선택한 날짜: {date}')

time = st.time_input('시간을 선택하세요', datetime.time(9, 0))
st.write(f'선택한 시간: {time}')

chart_type = st.radio(
    '차트 종류를 선택하세요',
    ['선 차트', '바 차트', '영역 차트']
)
st.write(f'선택: {chart_type}')

colors = st.multiselect(
    '좋아하는 색을 모두 선택하세요',
    ['빨강', '파랑', '초록', '노랑', '보라'],
    default=['파랑']
)
st.write(f'선택한 색: {colors}')

import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

import streamlit as st
import pandas as pd

df = pd.DataFrame({"이름": ["홍길동", "김철수"], "점수": [90, 85]})

st.download_button(
    label="CSV로 다운로드",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="결과.csv",
    mime="text/csv"
)

import time

placeholder = st.empty()
for i in range(10, 0, -1):
    placeholder.write(f'카운트다운: {i}')
    time.sleep(0.5)
placeholder.write('발사!')