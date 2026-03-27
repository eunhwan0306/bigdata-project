import streamlit as st
import pandas as pd
st.title('위젯 실습 - selectbox')

category = st.selectbox(
    '카테고리를 선택하세요',
    ['전자제품', '의류', '식품', '도서']
)
st.write(f'선택한 카테고리: **{category}**')

data = {
    '전자제품': {'평균가격': '₩35만', '판매량': 150},
    '의류': {'평균가격': '₩5만', '판매량': 320},
    '식품': {'평균가격': '₩1만', '판매량': 890},
    '도서': {'평균가격': '₩2만', '판매량': 210},
}

info = data[category]
st.write(f"평균 가격: {info['평균가격']}")
st.write(f"월 판매량: {info['판매량']}개")


import streamlit as st
st.title('위젯 실습 - slider')

age = st.slider('나이를 선택하세요', 0, 100, 25)
st.write(f'선택한 나이: {age}세')

price_range = st.slider(
    '가격 범위를 설정하세요',
    min_value=0,
    max_value=100000,
    value=(20000, 80000),
    step=5000,
    format='₩%d'
)
st.write(f'선택 범위: ₩{price_range[0]:,} ~ ₩{price_range[1]:,}')

import streamlit as st
import pandas as pd
st.title('위젯 실습 - selectbox')

category = st.selectbox(
    '카테고리를 선택하세요',
    ['전자제품', '의류', '식품', '도서']
)
st.write(f'선택한 카테고리: **{category}**')

data = {
    '전자제품': {'평균가격': '₩35만', '판매량': 150},
    '의류': {'평균가격': '₩5만', '판매량': 320},
    '식품': {'평균가격': '₩1만', '판매량': 890},
    '도서': {'평균가격': '₩2만', '판매량': 210},
}

info = data[category]
st.write(f"평균 가격: {info['평균가격']}")
st.write(f"월 판매량: {info['판매량']}개")


import streamlit as st
st.title('위젯 실습 - slider')

age = st.slider('나이를 선택하세요', 0, 100, 25)
st.write(f'선택한 나이: {age}세')

price_range = st.slider(
    '가격 범위를 설정하세요',
    min_value=0,
    max_value=100000,
    value=(20000, 80000),
    step=5000,
    format='₩%d'
)
st.write(f'선택 범위: ₩{price_range[0]:,} ~ ₩{price_range[1]:,}')