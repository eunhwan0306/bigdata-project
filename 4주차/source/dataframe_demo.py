import streamlit as st
import pandas as pd
import numpy as np

st.title('데이터 표시 실습')

df = pd.DataFrame(
    np.random.randn(20, 5),
    columns=['매출', '비용', '이익', '고객수', '만족도']
)

st.subheader('기본 데이터프레임')
st.dataframe(df)

st.subheader('스타일 적용된 데이터프레임')
st.dataframe(df.style.highlight_max(axis=0))

edited_df = st.data_editor(df)

st.write('수정된 데이터:', edited_df)