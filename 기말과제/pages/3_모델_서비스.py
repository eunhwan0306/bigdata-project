import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, recall_score
from src.data_loader import (
    load_incidents, load_accidents_history, load_weather,
    align_weather_to_incident, WEATHER_WEIGHT, ROUTE_BASE_RISK,
)
from src.features import (
    build_features, FEATURE_COLS, TARGET_COL,
    label_risk, WEATHER_DEFAULTS, ASOS_COLS,
)

st.title("🔮 위험도 예측 서비스")
st.caption("출발 노선·시각·기상 조건을 입력하면 연쇄 정체 위험도를 예측합니다.")


@st.cache_resource(show_spinner="모델 학습 중...")
def train_model():
    df_raw, _ = load_incidents(800)
    df_acc    = load_accidents_history()
    df_wx     = load_weather()
    # ASOS 기상 수치를 돌발상황 발생 시각 기준으로 nearest 매핑
    df_aligned = align_weather_to_incident(df_raw, df_wx)
    df = build_features(df_aligned, accident_df=df_acc)
    X = df[FEATURE_COLS].fillna(0)
    y = df[TARGET_COL]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        class_weight={0: 1.0, 1: 1.5, 2: 3.0},
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report   = classification_report(y_test, y_pred, output_dict=True)
    cm       = confusion_matrix(y_test, y_pred)
    acc      = accuracy_score(y_test, y_pred)
    high_risk_recall = recall_score(y_test, y_pred, labels=[2], average="macro", zero_division=0)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="f1_macro", n_jobs=-1)
    importance = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    return model, report, cm, acc, high_risk_recall, cv_scores, importance, df_acc


model, report, cm, acc, high_risk_recall, cv_scores, importance, _df_acc = train_model()


def _compute_hist_risk(route, df_acc):
    if df_acc is None or df_acc.empty:
        return ROUTE_BASE_RISK.get(route, 0.5)
    route_hist = df_acc.groupby("노선명").agg(
        총사고건수=("사고건수", "sum"),
        평균지연=("평균지연_분", "mean"),
    ).reset_index()
    max_cnt   = route_hist["총사고건수"].max() or 1
    max_delay = route_hist["평균지연"].max() or 1
    route_hist["이력_위험도"] = (
        0.6 * route_hist["총사고건수"] / max_cnt
        + 0.4 * route_hist["평균지연"] / max_delay
    ).clip(0, 1)
    return round(route_hist.set_index("노선명")["이력_위험도"].get(route, ROUTE_BASE_RISK.get(route, 0.5)), 3)


st.header("🗺 실시간 위험도 진단")
st.info("아래 조건을 입력하면 해당 노선의 연쇄 정체 위험도를 즉시 진단합니다.")

with st.form("predict_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        route     = st.selectbox("고속도로 노선", list(ROUTE_BASE_RISK.keys()))
        direction = st.radio("주행 방향", ["상행", "하행"], horizontal=True)
    with c2:
        hour    = st.slider("출발 시각 (시)", 0, 23, 8)
        weekday = st.selectbox("요일",
            ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"])
        dow = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"].index(weekday)
    with c3:
        weather    = st.selectbox("현재 기상 상태", list(WEATHER_DEFAULTS.keys()))
        controlled = st.number_input("통제 차로 수", 0, 4, 0, step=1)
        event_type = st.selectbox("돌발 유형",
            ["교통사고","공사","낙하물","기상악화","차량고장"])

    st.markdown("##### 🌡️ ASOS 기상 수치 (기상 상태 기반 자동 설정, 수동 조정 가능)")
    wx_def = WEATHER_DEFAULTS["맑음"]  # 폼 내부라 동적 기본값 불가 → 맑음 기준
    a1, a2, a3, a4, a5 = st.columns(5)
    temp_val = a1.number_input("기온 (℃)",    -20.0, 40.0,  wx_def["기온_℃"],   0.5)
    rain_val = a2.number_input("강수량 (mm)",   0.0,  80.0,  wx_def["강수량_mm"], 0.5)
    snow_val = a3.number_input("적설량 (cm)",   0.0,  50.0,  wx_def["적설량_cm"], 0.5)
    vis_val  = a4.number_input("시정 (km)",     0.0,  20.0,  wx_def["시정_km"],   0.5)
    wind_val = a5.number_input("풍속 (m/s)",    0.0,  20.0,  wx_def["풍속_m/s"],  0.5)

    submitted = st.form_submit_button("🔍 위험도 진단하기", use_container_width=True)

if submitted:
    weekend   = int(dow >= 5)
    is_peak   = int((7<=hour<=9 or 17<=hour<=19) and not weekend
                    or (11<=hour<=16 and weekend))
    weather_w  = WEATHER_WEIGHT.get(weather, 1.0)
    road_risk  = controlled * weather_w
    route_risk = ROUTE_BASE_RISK.get(route, 0.5)
    hist_risk  = _compute_hist_risk(route, _df_acc)

    feat = pd.DataFrame([{
        "월": 5, "시간": hour, "요일": dow, "주말여부": weekend,
        "피크타임_여부": is_peak,
        "통제차로수": controlled,
        "기상_위험가중치": weather_w,
        "도로_폐쇄_위험도": road_risk,
        "노선_기본위험도": route_risk,
        "이력_위험도": hist_risk,
        "사고_여부": int(event_type=="교통사고"),
        "공사_여부": int(event_type=="공사"),
        "기상악화_여부": int(event_type=="기상악화"),
        "기온_℃":    temp_val,
        "강수량_mm":  rain_val,
        "적설량_cm":  snow_val,
        "시정_km":    vis_val,
        "풍속_m/s":   wind_val,
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
        | 노선 이력 위험도 | {hist_risk} |
        | 강수량 | {rain_val} mm |
        | 적설량 | {snow_val} cm |
        | 시정 | {vis_val} km |
        | 풍속 | {wind_val} m/s |
        | 기온 | {temp_val} ℃ |
        """)


st.divider()
st.header("📊 모델 성능 평가")

st.info(
    "**고위험 재현율(Recall)** 을 최우선 지표로 사용합니다. "
    "위험을 놓치는 False Negative 가 잘못된 경보(False Positive) 보다 훨씬 큰 피해를 유발하기 때문입니다.",
    icon="⚠️",
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("정확도(Accuracy)",  f"{acc*100:.1f}%")
m2.metric("정밀도(Macro)",     f"{report['macro avg']['precision']*100:.1f}%")
m3.metric("재현율(Macro)",     f"{report['macro avg']['recall']*100:.1f}%")
m4.metric("F1(Macro)",        f"{report['macro avg']['f1-score']*100:.1f}%")
m5.metric("🔴 고위험 재현율", f"{high_risk_recall*100:.1f}%",
          help="고위험(2등급) 실제 케이스 중 모델이 올바르게 감지한 비율.")

st.subheader("5-Fold 교차검증 F1-Macro")
cv_col1, cv_col2 = st.columns([2, 1])
with cv_col1:
    cv_df = pd.DataFrame({
        "Fold": [f"Fold {i+1}" for i in range(len(cv_scores))],
        "F1-Macro": cv_scores.round(4),
    })
    fig = px.bar(cv_df, x="Fold", y="F1-Macro",
                 color="F1-Macro", color_continuous_scale="Teal",
                 range_y=[max(0, cv_scores.min()-0.05), 1.0])
    fig.add_hline(y=cv_scores.mean(), line_dash="dash", line_color="#facc15",
                  annotation_text=f"평균 {cv_scores.mean():.4f}")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with cv_col2:
    st.metric("CV 평균 F1",  f"{cv_scores.mean():.4f}")
    st.metric("CV 표준편차", f"±{cv_scores.std():.4f}")
    st.caption("표준편차가 작을수록 모델이 안정적으로 일반화됩니다.")

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
            "등급":   name,
            "정밀도": round(report[cls]["precision"]*100, 1),
            "재현율": round(report[cls]["recall"]*100, 1),
            "F1":    round(report[cls]["f1-score"]*100, 1),
            "지원수": report[cls]["support"],
        })
perf_df = pd.DataFrame(perf)

def highlight_recall(row):
    styles = [""] * len(row)
    idx = perf_df.columns.get_loc("재현율")
    if row["등급"] == "고위험":
        styles[idx] = "background-color: rgba(248,113,113,0.3); font-weight: bold"
    return styles

st.dataframe(
    perf_df.style.apply(highlight_recall, axis=1),
    use_container_width=True,
    hide_index=True,
)

with st.expander("💡 모델 설명"):
    st.markdown(f"""
    **Random Forest Classifier** (scikit-learn)
    - 트리 기반 앙상블 — 다수의 결정 트리를 병렬 학습 후 다수결
    - 800건 시뮬레이션 데이터, Train/Test = 80:20 (stratified) + 5-Fold 교차검증
    - **class_weight = {{저:1.0, 중:1.5, 고:3.0}}** — 고위험 과소 탐지 방지
    - **{len(FEATURE_COLS)}개 피처**: 시간대, 기상가중치, 노선위험도, 이력위험도 + **ASOS 수치 기상 5종**
    - 주요 평가 지표: 고위험 **재현율(Recall)** — False Negative(위험 누락) 최소화 목표
    """)
