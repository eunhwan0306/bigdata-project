import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_incidents, load_accidents_history, load_weather, align_weather_to_incident
from src.features import build_features

st.title("📊 데이터 탐색 (EDA)")
st.caption("돌발상황·교통사고 이력·기상 데이터의 기본 통계와 결측 현황을 탐색합니다.")

with st.spinner("데이터 불러오는 중..."):
    df_raw, source = load_incidents(800)
    df_acc = load_accidents_history()
    df_wx  = load_weather()

source_label = {"api": "🌐 실시간 API", "csv": "📂 로컬 CSV", "simulation": "🔄 시뮬레이션"}
st.toast(f"{source_label[source]} 데이터를 사용합니다.", icon="📡")

df_aligned = align_weather_to_incident(df_raw, df_wx)
df = build_features(df_aligned, accident_df=df_acc)

tab1, tab2, tab3 = st.tabs(["돌발상황 요약", "결측치 분석", "교통사고 이력"])

with tab1:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("전체 건수",    f"{len(df):,}건")
    k2.metric("고위험 건수",  f"{(df['위험_등급']==2).sum():,}건",
              delta=f"{(df['위험_등급']==2).mean()*100:.1f}%")
    k3.metric("평균 통제차로수", f"{df['통제차로수'].mean():.2f}개")
    k4.metric("평균 지속시간", f"{df['지속시간_분'].mean():.0f}분")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("사고 유형 분포")
        cnt = df["사고유형"].value_counts().reset_index()
        cnt.columns = ["유형", "건수"]
        fig = px.bar(cnt, x="유형", y="건수", color="유형",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("위험 등급 분포")
        grade_map = {0: "저위험", 1: "중위험", 2: "고위험"}
        grade_cnt = df["위험_등급"].map(grade_map).value_counts().reset_index()
        grade_cnt.columns = ["등급", "건수"]
        fig = px.pie(grade_cnt, names="등급", values="건수", hole=0.4,
                     color="등급",
                     color_discrete_map={"저위험": "#22d3ee", "중위험": "#facc15", "고위험": "#f87171"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("기초 통계량")
    num_cols = ["통제차로수", "지속시간_분", "위험도_점수", "기상_위험가중치", "도로_폐쇄_위험도"]
    st.dataframe(df[num_cols].describe().round(3), use_container_width=True)

    st.subheader("기상 상태별 위험도 점수 분포")
    fig = px.box(df, x="기상상태", y="위험도_점수", color="기상상태",
                 category_orders={"기상상태": ["맑음", "흐림", "비", "안개", "눈"]},
                 color_discrete_sequence=["#22d3ee", "#94a3b8", "#60a5fa", "#a78bfa", "#f0abfc"])
    fig.update_layout(showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)


with tab2:
    st.subheader("돌발상황 데이터 결측치 현황")
    missing = df.isnull().sum().reset_index()
    missing.columns = ["컬럼", "결측수"]
    missing["결측률(%)"] = (missing["결측수"] / len(df) * 100).round(2)
    missing["결측여부"] = missing["결측수"].apply(lambda x: "결측 있음" if x > 0 else "완전")
    color_map = {"결측 있음": "#f87171", "완전": "#22d3ee"}
    fig = px.bar(missing, x="컬럼", y="결측률(%)", color="결측여부",
                 color_discrete_map=color_map, text="결측수")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(missing, use_container_width=True)

    with st.expander("💡 결측치 처리 전략"):
        st.markdown("""
        | 컬럼 | 처리 방법 | 이유 |
        |------|-----------|------|
        | `통제차로수` | 0으로 대체 | 미통제 상태 의미 |
        | `기상상태` | '맑음' 대체 | 기상 정보 없으면 정상으로 간주 |
        | `위험도_점수` | 파생변수로 재계산 | 원본 결측 시 공식으로 보완 |
        | `지속시간_분` | 중앙값 대체 | 이상치 영향 최소화 |
        """)


with tab3:
    st.subheader("노선별 연도별 교통사고 현황 (2019~2024)")
    fig = px.line(df_acc, x="연도", y="사고건수", color="노선명",
                  markers=True,
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("노선별 평균 사고건수")
        avg_acc = df_acc.groupby("노선명")["사고건수"].mean().sort_values(ascending=True)
        fig = px.bar(avg_acc.reset_index(), x="사고건수", y="노선명", orientation="h",
                     color="사고건수", color_continuous_scale="Reds")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("노선별 평균 정체 지연시간(분)")
        avg_delay = df_acc.groupby("노선명")["평균지연_분"].mean().sort_values(ascending=True)
        fig = px.bar(avg_delay.reset_index(), x="평균지연_분", y="노선명", orientation="h",
                     color="평균지연_분", color_continuous_scale="Oranges")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("교통사고 이력 원본 데이터")
    st.dataframe(df_acc, use_container_width=True)

