"""
data_loader.py
국토교통부 돌발상황 API → 로컬 CSV → 시뮬레이션 순서로 데이터 제공
"""
import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

_DATA_DIR = Path(__file__).parent.parent / "data"
_INCIDENTS_CSV = _DATA_DIR / "incidents_sample.csv"
_ACCIDENTS_CSV = _DATA_DIR / "accidents_history.csv"
_WEATHER_CSV   = _DATA_DIR / "weather_history.csv"

API_KEY = os.getenv("API_KEY", "")

ROUTE_BASE_RISK = {
    "경부고속도로":      0.82,
    "서해안고속도로":    0.74,
    "남해고속도로":      0.68,
    "중부고속도로":      0.61,
    "영동고속도로":      0.77,
    "호남고속도로":      0.55,
    "중앙고속도로":      0.63,
    "동해고속도로":      0.49,
    "통영대전고속도로":  0.58,
    "광주대구고속도로":  0.52,
}

WEATHER_WEIGHT = {"맑음": 1.0, "흐림": 1.2, "비": 1.5, "안개": 1.8, "눈": 2.0}
EVENT_TYPES    = ["교통사고", "공사", "낙하물", "기상악화", "차량고장"]
DIRECTIONS     = ["상행", "하행"]


def _fetch_its_api(rows=100):
    if not API_KEY:
        return None
    url = (
        "https://openapi.its.go.kr:9443/trafficInfo"
        f"?apiKey={API_KEY}&type=json&numOfRows={rows}&pageNo=1"
    )
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        items = data.get("body", {}).get("items", {}).get("item", [])
        if not items:
            return None
        df = pd.DataFrame(items)
        df = df.rename(columns={
            "eventType": "사고유형", "roadName": "노선명",
            "occurTime": "공지일시", "laneCount": "통제차로수",
            "eventContent": "돌발내용", "lat": "위도", "lng": "경도",
        })
        return df
    except Exception:
        return None


def _load_local_csv():
    if _INCIDENTS_CSV.exists():
        df = pd.read_csv(_INCIDENTS_CSV, encoding="utf-8-sig", parse_dates=["공지일시"])
        if len(df) > 10:
            return df
    return None


def _hour_weights():
    w = [1.0] * 24
    for h in [7, 8, 9, 17, 18, 19]:
        w[h] = 3.0
    for h in [11, 12, 13, 14, 15, 16]:
        w[h] = 1.8
    for h in [0, 1, 2, 3, 4, 5]:
        w[h] = 0.4
    total = sum(w)
    return [x / total for x in w]


def _generate_incidents(n=800):
    rng = np.random.default_rng(42)
    routes = list(ROUTE_BASE_RISK.keys())

    hours  = rng.choice(range(24), n, p=_hour_weights())
    months = rng.choice(range(1, 13), n)
    days   = rng.choice(range(1, 29), n)
    dow    = rng.choice(range(7), n)

    route_idx   = rng.choice(len(routes), n)
    route_names = [routes[i] for i in route_idx]

    weather_prob = [0.40, 0.25, 0.15, 0.12, 0.08]
    weathers = rng.choice(list(WEATHER_WEIGHT.keys()), n, p=weather_prob)

    event_prob = [0.42, 0.28, 0.10, 0.10, 0.10]
    events = rng.choice(EVENT_TYPES, n, p=event_prob)

    controlled_lanes = rng.choice([0, 1, 2, 3], n, p=[0.35, 0.40, 0.18, 0.07])
    duration_min = rng.integers(10, 180, n)

    base_risks = np.array([ROUTE_BASE_RISK[r] for r in route_names])
    weather_w  = np.array([WEATHER_WEIGHT[w] for w in weathers])
    risk_score = controlled_lanes * weather_w * base_risks

    risk_level = pd.cut(risk_score, bins=[-0.1, 0.5, 1.5, 10],
                        labels=[0, 1, 2]).astype(int)

    dates = pd.to_datetime({
        "year": 2024, "month": months, "day": days,
        "hour": hours, "minute": rng.integers(0, 60, n)
    })

    df = pd.DataFrame({
        "공지일시":    dates,
        "노선명":      route_names,
        "사고유형":    events,
        "주행방향":    rng.choice(DIRECTIONS, n),
        "통제차로수":  controlled_lanes,
        "기상상태":    weathers,
        "지속시간_분": duration_min,
        "위험도_점수": risk_score.round(3),
        "위험_등급":   risk_level,
        "위도":        rng.uniform(34.5, 38.5, n).round(5),
        "경도":        rng.uniform(126.5, 129.5, n).round(5),
    })
    return df.sort_values("공지일시").reset_index(drop=True)


def _generate_accidents_history():
    rng = np.random.default_rng(7)
    routes = list(ROUTE_BASE_RISK.keys())
    rows = []
    for year in range(2019, 2025):
        for route in routes:
            base = ROUTE_BASE_RISK[route]
            cnt = int(rng.normal(base * 120, 20))
            rows.append({
                "연도": year, "노선명": route,
                "사고건수": max(cnt, 5),
                "사망자수": int(rng.poisson(base * 3)),
                "부상자수": int(rng.normal(base * 40, 8)),
                "평균지연_분": round(rng.normal(base * 35, 10), 1),
                "노선_위험도": round(base, 3),
            })
    return pd.DataFrame(rows)


def _generate_weather_history(n=500):
    rng = np.random.default_rng(99)
    stations = ["서울", "수원", "대전", "대구", "부산", "광주", "강릉", "청주"]
    hours  = rng.choice(range(24), n)
    months = rng.choice(range(1, 13), n)
    days   = rng.choice(range(1, 29), n)

    precip = np.where(rng.random(n) < 0.15, rng.exponential(5, n), 0.0)
    snow   = np.where((months <= 2) | (months == 12),
                      np.where(rng.random(n) < 0.1, rng.exponential(3, n), 0.0), 0.0)
    vis    = np.where(rng.random(n) < 0.08, rng.uniform(0.2, 1.0, n), rng.uniform(5, 20, n))
    temp_base = 15 - np.abs(months - 6.5) * 2.5
    temp = rng.normal(temp_base, 5, n)

    weather_cond = []
    for i in range(n):
        if snow[i] > 0:        weather_cond.append("눈")
        elif vis[i] < 1.0:     weather_cond.append("안개")
        elif precip[i] > 0:    weather_cond.append("비")
        elif rng.random() < 0.3: weather_cond.append("흐림")
        else:                   weather_cond.append("맑음")

    dates = pd.to_datetime({
        "year": 2024, "month": months, "day": days, "hour": hours, "minute": 0
    })
    return pd.DataFrame({
        "일시": dates, "지점명": rng.choice(stations, n),
        "기온_℃": temp.round(1), "강수량_mm": precip.round(1),
        "적설량_cm": snow.round(1), "시정_km": vis.round(2),
        "풍속_m/s": rng.exponential(3, n).round(1),
        "습도_%": rng.uniform(30, 100, n).round(0),
        "기상상태": weather_cond,
    }).sort_values("일시").reset_index(drop=True)


@st.cache_data(ttl="1h", show_spinner=False)
def load_incidents(n=800):
    df = _fetch_its_api(n)
    if df is not None and len(df) > 10:
        return df, "api"
    df = _load_local_csv()
    if df is not None:
        return df, "csv"
    df = _generate_incidents(n)
    _DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(_INCIDENTS_CSV, index=False, encoding="utf-8-sig")
    return df, "simulation"


@st.cache_data(ttl="24h", show_spinner=False)
def load_accidents_history():
    if _ACCIDENTS_CSV.exists():
        return pd.read_csv(_ACCIDENTS_CSV, encoding="utf-8-sig")
    df = _generate_accidents_history()
    _DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(_ACCIDENTS_CSV, index=False, encoding="utf-8-sig")
    return df


@st.cache_data(ttl="1h", show_spinner=False)
def load_weather():
    if _WEATHER_CSV.exists():
        return pd.read_csv(_WEATHER_CSV, encoding="utf-8-sig", parse_dates=["일시"])
    df = _generate_weather_history()
    _DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(_WEATHER_CSV, index=False, encoding="utf-8-sig")
    return df


def get_route_list():
    return list(ROUTE_BASE_RISK.keys())


def get_route_risk_map():
    return ROUTE_BASE_RISK.copy()
