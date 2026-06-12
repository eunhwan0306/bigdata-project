"""
features.py - 돌발상황 데이터 특성 엔지니어링

타깃 라벨링(혼합 방식):
  - 과거 사고 이력(accident_df)로 노선별 이력_위험도 산정 (사고건수·지연시간 정규화 6:4)
  - 실시간 돌발상황(통제차로수 × 기상가중치)으로 보정
  - 두 요소를 6:4로 합산 → 0(저) / 1(중) / 2(고) 3등급 분류

ASOS 연결:
  - align_weather_to_incident() 으로 merge_asof 매핑된 수치형 기상 컬럼 사용
  - 기온, 강수량, 적설량, 시정, 풍속 → FEATURE_COLS 에 포함
"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data_loader import WEATHER_WEIGHT, ROUTE_BASE_RISK

# 기상상태별 ASOS 수치 기본값 (API 누락·예측 폼 입력 대체용)
WEATHER_DEFAULTS = {
    "맑음": {"기온_℃": 15.0, "강수량_mm": 0.0, "적설량_cm": 0.0, "시정_km": 15.0, "풍속_m/s": 2.0},
    "흐림": {"기온_℃": 12.0, "강수량_mm": 0.0, "적설량_cm": 0.0, "시정_km":  8.0, "풍속_m/s": 3.0},
    "비":   {"기온_℃": 10.0, "강수량_mm": 8.0, "적설량_cm": 0.0, "시정_km":  3.0, "풍속_m/s": 4.0},
    "안개": {"기온_℃":  8.0, "강수량_mm": 0.0, "적설량_cm": 0.0, "시정_km":  0.5, "풍속_m/s": 1.5},
    "눈":   {"기온_℃": -2.0, "강수량_mm": 0.0, "적설량_cm": 5.0, "시정_km":  2.0, "풍속_m/s": 3.5},
}
ASOS_COLS = ["기온_℃", "강수량_mm", "적설량_cm", "시정_km", "풍속_m/s"]


def add_temporal_features(df):
    df = df.copy()
    dt = pd.to_datetime(df["공지일시"])
    df["월"]      = dt.dt.month
    df["시간"]    = dt.dt.hour
    df["요일"]    = dt.dt.dayofweek
    df["주말여부"] = (df["요일"] >= 5).astype(int)

    def _is_peak(row):
        h = row["시간"]
        if row["주말여부"] == 0:
            return int(7 <= h <= 9 or 17 <= h <= 19)
        return int(11 <= h <= 16)

    df["피크타임_여부"] = df.apply(_is_peak, axis=1)
    return df


def add_physical_risk(df):
    df = df.copy()
    df["기상_위험가중치"] = df["기상상태"].map(WEATHER_WEIGHT).fillna(1.0)
    df["도로_폐쇄_위험도"] = (df["통제차로수"] * df["기상_위험가중치"]).round(3)
    return df


def add_route_risk(df, train_df=None):
    df = df.copy()
    if train_df is not None:
        risk_map = train_df.groupby("노선명")["위험_등급"].mean().to_dict()
    else:
        risk_map = ROUTE_BASE_RISK
    df["노선_기본위험도"] = df["노선명"].map(risk_map).fillna(0.5)
    return df


def add_historical_route_risk(df, accident_df=None):
    """과거 사고 이력으로부터 노선별 이력 위험도를 산정하여 피처로 추가한다.

    이력_위험도 = 0.6 * (노선_사고건수 / 전체최대) + 0.4 * (평균지연_분 / 전체최대)
    """
    df = df.copy()
    if accident_df is None or len(accident_df) == 0:
        df["이력_위험도"] = df["노선명"].map(ROUTE_BASE_RISK).fillna(0.5)
        return df

    route_hist = accident_df.groupby("노선명").agg(
        총사고건수=("사고건수", "sum"),
        평균지연=("평균지연_분", "mean"),
    ).reset_index()

    max_cnt   = route_hist["총사고건수"].max() or 1
    max_delay = route_hist["평균지연"].max() or 1

    route_hist["이력_위험도"] = (
        0.6 * route_hist["총사고건수"] / max_cnt
        + 0.4 * route_hist["평균지연"] / max_delay
    ).clip(0, 1).round(3)

    risk_map = route_hist.set_index("노선명")["이력_위험도"].to_dict()
    df["이력_위험도"] = df["노선명"].map(risk_map).fillna(0.5)
    return df


def add_asos_features(df):
    """ASOS 수치형 기상 컬럼을 추가하고 결측치를 기상상태 기반 기본값으로 채운다.

    align_weather_to_incident() 가 먼저 호출된 경우 실측값이 이미 있고,
    누락된 행만 WEATHER_DEFAULTS 로 보완한다.
    미호출 시 전체를 기본값으로 생성한다.
    """
    df = df.copy()
    for col in ASOS_COLS:
        if col not in df.columns:
            df[col] = df["기상상태"].map(
                lambda w: WEATHER_DEFAULTS.get(w, WEATHER_DEFAULTS["맑음"]).get(col, 0.0)
            )
        else:
            mask = df[col].isna()
            if mask.any():
                df.loc[mask, col] = df.loc[mask, "기상상태"].map(
                    lambda w: WEATHER_DEFAULTS.get(w, WEATHER_DEFAULTS["맑음"]).get(col, 0.0)
                )
    return df


def add_event_flags(df):
    df = df.copy()
    df["사고_여부"]     = (df["사고유형"] == "교통사고").astype(int)
    df["공사_여부"]     = (df["사고유형"] == "공사").astype(int)
    df["기상악화_여부"] = (df["사고유형"] == "기상악화").astype(int)
    return df


RISK_LABEL = {0: "저위험", 1: "중위험", 2: "고위험"}
RISK_ICON  = {0: "🟢 저위험", 1: "🟡 중위험", 2: "🔴 고위험"}
RISK_COLOR = {0: "#22d3ee", 1: "#facc15", 2: "#f87171"}


def label_risk(level):
    return RISK_ICON.get(int(level), "알 수 없음")


def color_risk(level):
    return RISK_COLOR.get(int(level), "#94a3b8")


def build_features(df, train_df=None, accident_df=None):
    """피처 파이프라인.

    accident_df : 과거 사고 이력 → 이력_위험도 산정
    ASOS 컬럼은 align_weather_to_incident() 호출 후 df 에 이미 있거나,
    없으면 add_asos_features() 에서 기상상태 기반 기본값으로 채운다.
    """
    df = add_temporal_features(df)
    df = add_physical_risk(df)
    df = add_route_risk(df, train_df)
    df = add_historical_route_risk(df, accident_df)
    df = add_asos_features(df)
    df = add_event_flags(df)
    return df


FEATURE_COLS = [
    "월", "시간", "요일", "주말여부", "피크타임_여부",
    "통제차로수", "기상_위험가중치", "도로_폐쇄_위험도",
    "노선_기본위험도", "이력_위험도",
    "사고_여부", "공사_여부", "기상악화_여부",
    "기온_℃", "강수량_mm", "적설량_cm", "시정_km", "풍속_m/s",
]
TARGET_COL = "위험_등급"
