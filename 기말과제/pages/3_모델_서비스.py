import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from src.data_loader import load_incidents, WEATHER_WEIGHT, ROUTE_BASE_RISK
from src.features import build_features, FEATURE_COLS, TARGET_COL, label_risk

st.title("🔮 위험도 예측 서비스")
st.caption("출발 노선·시각·기상 조건을 입력하면 연쇄 정체 위험도를 예측합니다.")


@st.cache_resource(show_spinner="모델 학습 중...")
def train_model():
    df_raw, _ = load_incidents(800)
    df = build_features(df_raw)
    X = df[FEATURE_COLS].fillna(0)
    y = df[TARGET_COL]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.08, random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    acc = accuracy_score(y_test, y_pred)
    importance = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    return model, report, cm, acc, importance


model, report, cm, acc, importance = train_model()

st.header("🗺 실시간 위험도 진단")
st.info("아래 조건을 입력하면 해당 노선의 연쇄 정체 위험도를 즉시 진단합니다.")

with st.form("predict_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        route    = st.selectbox("고속도로 노선", list(ROUTE_BASE_RISK.keys()))
        direction = st.radio("주행 방향", ["상행", "하행"], horizontal=True)
    with c2:
        hour    = st.slider("출발 시각 (시)", 0, 23, 8)
        weekday = st.selectbox("요일",
            ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"])
        dow = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"].index(weekday)
    with c3:
        weather    = st.selectbox("현재 기상 상태", ["맑음","흐림","비","안개","눈"])
        controlled = st.number_input("통제 차로 수", 0, 4, 0, step=1)
        event_type = st.selectbox("돌발 유형",
            ["교통사고","공사","낙하물","기상악화","차량고장"])
    submitted = st.form_submit_button("🔍 위험도 진단하기", use_container_width=True)

if submitted:
    weekend  = int(dow >= 5)
    is_peak  = int((7<=hour<=9 or 17<=hour<=19) and not weekend
                   or (11<=hour<=16 and weekend))
    weather_w = WEATHER_WEIGHT.get(weather, 1.0)
    road_risk = controlled * weather_w
    route_risk = ROUTE_BASE_RISK.get(route, 0.5)

    feat = pd.DataFrame([{
        "월": 5, "시간": hour, "요일": dow, "주말여부": weekend,
        "피크타임_여부": is_peak,
        "통제차로수": controlled,
        "기상_위험가중치": weather_w,
        "도로_폐쇄_위험도": road_risk,
        "노선_기본위험도": route_risk,
        "사고_여부": int(event_type=="교통사고"),
        "공사_여부": int(event_type=="공사"),
        "기상악화_여부": int(event_type=="기상악화"),
    }])

    pred = model.predict(feat)[0]
    prob = model.predict_proba(feat)[0]

    risk_colors = {0:"#22d3ee", 1:"#facc15", 2:"#f87171"}
    risk_bg     = {0:"rgba(34,211,238,0.12)", 1:"rgba(250,204,21,0.12)", 2:"rgba(248,113,113,0.15)"}

    st.markdown("---")
    st.markdown(f"""
    <div style="background:{risk_bg[pred]};border-radius:12px;padding:24px;border:2px solid {risk_colors[pred]}">
        <h2 style="color:{risk_colors[pred]};margin:0">{label_risk(pred)}</h2>
        <p style="font-size:1.1rem;color:#f8fafc;margin-top:8px">
            <strong>{route}</strong> {direction} — {hour}시 출발 / {weather} / 통제 {controlled}차로
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(" ")
    p1, p2, p3 = st.columns(3)
    p1.metric("🟢 저위험 확률", f"{prob[0]*100:.1f}%")
    p2.metric("🟡 중위험 확률", f"{prob[1]*100:.1f}%")
    p3.metric("🔴 고위험 확률", f"{prob[2]*100:.1f}%")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(prob[2]*100, 1),
        title={"text": "고위험 확률 (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": risk_colors[pred]},
            "steps": [
                {"range": [0, 33],   "color": "rgba(34,211,238,0.2)"},
                {"range": [33, 66],  "color": "rgba(250,204,21,0.2)"},
                {"range": [66, 100], "color": "rgba(248,113,113,0.2)"},
            ],
        }
    ))
    fig.update_layout(height=280,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

    if pred == 2:
        st.error("⚠️ **고위험** — 연쇄 정체 가능성이 높습니다. 출발 지연 또는 대체 노선 이용을 권장합니다.")
    elif pred == 1:
        st.warning("🟡 **중위험** — 기상 악화 시 정체가 심화될 수 있습니다. 안전거리 확보를 권장합니다.")
    else:
        st.success("🟢 **저위험** — 현재 조건에서 연쇄 정체 위험이 낮습니다.")

    with st.expander("📐 계산 상세"):
        st.markdown(f"""
        | 파생변수 | 값 |
        |---------|-----|
        | 피크타임 여부 | {'✅ 해당' if is_peak else '❌ 비해당'} |
        | 기상 위험가중치 | {weather_w}× |
        | 도로 폐쇄 위험도 | {controlled} × {weather_w} = **{road_risk}** |
        | 노선 기본 위험도 | {route_risk} |
        | 종합 위험도 점수 | {road_risk * route_risk:.3f} |
        """)


st.divider()
st.header("📊 모델 성능 평가")

m1, m2, m3, m4 = st.columns(4)
m1.metric("정확도", f"{acc*100:.1f}%")
m2.metric("정밀도(Macro)", f"{report['macro avg']['precision']*100:.1f}%")
m3.metric("재현율(Macro)", f"{report['macro avg']['recall']*100:.1f}%")
m4.metric("F1(Macro)",    f"{report['macro avg']['f1-score']*100:.1f}%")

col1, col2 = st.columns(2)
with col1:
    st.subheader("혼동 행렬")
    grade_names = ["저위험(0)", "중위험(1)", "고위험(2)"]
    cm_df = pd.DataFrame(cm, index=grade_names, columns=grade_names)
    fig = px.imshow(cm_df, text_auto=True, color_continuous_scale="Blues",
                    labels={"x":"예측","y":"실제","color":"건수"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("특성 중요도")
    imp_df = importance.reset_index()
    imp_df.columns = ["특성", "중요도"]
    fig = px.bar(imp_df, x="중요도", y="특성", orientation="h",
                 color="중요도", color_continuous_scale="Viridis")
    fig.update_layout(yaxis={"categoryorder":"total ascending"},
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("클래스별 성능 지표")
perf = []
for cls, name in zip(["0","1","2"], ["저위험","중위험","고위험"]):
    if cls in report:
        perf.append({
            "등급": name,
            "정밀도": round(report[cls]["precision"]*100, 1),
            "재현율": round(report[cls]["recall"]*100, 1),
            "F1":    round(report[cls]["f1-score"]*100, 1),
            "지원수": report[cls]["support"],
        })
st.dataframe(pd.DataFrame(perf), use_container_width=True, hide_index=True)

with st.expander("💡 모델 설명"):
    st.markdown("""
    **Gradient Boosting Classifier** (scikit-learn)
    - 트리 기반 앙상블 — 이전 트리의 잔차를 순차 학습
    - 800건 시뮬레이션 데이터 Train/Test = 80:20
    - 12개 파생변수(시간대, 기상가중치, 노선위험도 등) → 3등급 위험도 출력
    """)
