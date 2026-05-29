import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.data_loader import load_incidents, load_weather
from src.features import build_features

st.title("📈 시각화")
st.caption("노선별·시간대별·기상별 돌발상황 패턴을 다각도로 시각화합니다.")

with st.spinner("데이터 불러오는 중..."):
    df_raw, _ = load_incidents(800)

df = build_features(df_raw)

tab1, tab2, tab3, tab4 = st.tabs(["시간대 분석", "노선별 위험도", "기상 상관관계", "히트맵"])

with tab1:
    st.subheader("시간대별 돌발상황 발생 빈도")
    hourly = df.groupby(["시간", "위험_등급"]).size().reset_index(name="건수")
    grade_map = {0: "저위험", 1: "중위험", 2: "고위험"}
    hourly["등급명"] = hourly["위험_등급"].map(grade_map)
    fig = px.bar(hourly, x="시간", y="건수", color="등급명", barmode="stack",
                 color_discrete_map={"저위험": "#22d3ee", "중위험": "#facc15", "고위험": "#f87171"},
                 labels={"시간": "시간 (0~23시)", "건수": "발생 건수"})
    for start, end in [(7, 9), (17, 19)]:
        fig.add_vrect(x0=start-0.5, x1=end+0.5, fillcolor="yellow",
                      opacity=0.08, line_width=0, annotation_text="피크타임")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("요일별 평균 위험도")
        dow_map = {0:"월",1:"화",2:"수",3:"목",4:"금",5:"토",6:"일"}
        dow_risk = df.groupby("요일")["위험도_점수"].mean().reset_index()
        dow_risk["요일명"] = dow_risk["요일"].map(dow_map)
        fig = px.bar(dow_risk, x="요일명", y="위험도_점수",
                     color="위험도_점수", color_continuous_scale="RdYlGn_r",
                     category_orders={"요일명": ["월","화","수","목","금","토","일"]})
        fig.update_layout(showlegend=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("월별 사고 건수 추이")
        mon_cnt = df.groupby("월").size().reset_index(name="건수")
        fig = px.line(mon_cnt, x="월", y="건수", markers=True,
                      color_discrete_sequence=["#22d3ee"])
        fig.update_xaxes(tickvals=list(range(1,13)),
                         ticktext=["1월","2월","3월","4월","5월","6월",
                                   "7월","8월","9월","10월","11월","12월"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("노선별 평균 위험도 점수")
    route_risk = (
        df.groupby("노선명")
          .agg(평균위험도=("위험도_점수","mean"),
               총건수=("위험도_점수","count"),
               고위험건수=("위험_등급", lambda x: (x==2).sum()))
          .sort_values("평균위험도", ascending=False).reset_index()
    )
    route_risk["고위험비율(%)"] = (route_risk["고위험건수"]/route_risk["총건수"]*100).round(1)
    fig = px.bar(route_risk, x="평균위험도", y="노선명", orientation="h",
                 color="평균위험도", color_continuous_scale="RdYlGn_r",
                 text="고위험비율(%)")
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(yaxis={"categoryorder":"total ascending"},
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("노선별 사고 유형 구성")
    route_type = df.groupby(["노선명","사고유형"]).size().reset_index(name="건수")
    fig = px.bar(route_type, x="노선명", y="건수", color="사고유형", barmode="stack",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(xaxis_tickangle=-30,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("기상 상태별 위험도 분포")
    fig = px.violin(df, x="기상상태", y="위험도_점수", color="기상상태", box=True,
                    category_orders={"기상상태":["맑음","흐림","비","안개","눈"]},
                    color_discrete_sequence=["#22d3ee","#94a3b8","#60a5fa","#a78bfa","#f0abfc"])
    fig.update_layout(showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("통제차로수 vs 위험도 점수")
        fig = px.scatter(df, x="통제차로수", y="위험도_점수", color="기상상태",
                         size="지속시간_분", opacity=0.7,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("수치 특성 간 상관계수 히트맵")
        num_cols = ["통제차로수","지속시간_분","위험도_점수",
                    "기상_위험가중치","도로_폐쇄_위험도","노선_기본위험도",
                    "피크타임_여부","주말여부"]
        corr = df[num_cols].corr().round(3)
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("시간대 × 요일 사고 발생 히트맵")
    dow_map = {0:"월",1:"화",2:"수",3:"목",4:"금",5:"토",6:"일"}
    heat = df.groupby(["요일","시간"]).size().reset_index(name="건수")
    heat["요일명"] = heat["요일"].map(dow_map)
    heat_pivot = heat.pivot(index="요일명", columns="시간", values="건수").fillna(0)
    heat_pivot = heat_pivot.reindex(["월","화","수","목","금","토","일"])
    fig = px.imshow(heat_pivot, text_auto=True, color_continuous_scale="YlOrRd",
                    labels={"x":"시간(0~23)","y":"요일","color":"건수"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("노선 × 기상상태 위험도 히트맵")
    rw = df.groupby(["노선명","기상상태"])["위험도_점수"].mean().reset_index()
    rw_pivot = rw.pivot(index="노선명", columns="기상상태", values="위험도_점수").fillna(0)
    rw_pivot = rw_pivot.reindex(columns=["맑음","흐림","비","안개","눈"])
    fig = px.imshow(rw_pivot.round(2), text_auto=True, color_continuous_scale="RdYlGn_r",
                    labels={"color":"평균 위험도"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)
