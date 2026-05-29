"""
features.py - 돌발상황 데이터 특성 엔지니어링
계획서 3절 파생변수 전략 구현
"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data_loader import WEATHER_WEIGHT, ROUTE_BASE_RISK


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


def build_features(df, train_df=None):
    df = add_temporal_features(df)
    df = add_physical_risk(df)
    df = add_route_risk(df, train_df)
    df = add_event_flags(df)
    return df


FEATURE_COLS = [
    "월", "시간", "요일", "주말여부", "피크타임_여부",
    "통제차로수", "기상_위험가중치", "도로_폐쇄_위험도",
    "노선_기본위험도", "사고_여부", "공사_여부", "기상악화_여부",
]
TARGET_COL = "위험_등급"
