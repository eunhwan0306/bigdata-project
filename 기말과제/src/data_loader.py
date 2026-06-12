"""
data_loader.py
국토교통부 돌발상황 API → 로컬 CSV → 시뮬레이션 순서로 데이터 제공

API 안정성:
  - 재시도 로직: MAX_RETRIES=3, timeout=8s
  - SSL: verify=False (ITS Korea 인증서 우회)
  - 결측치: 통제차로수→0, 기상상태→맑음, 지속시간→중앙값
  - 시간 정합성: align_weather_to_incident() 로 ASOS 관측과 최근접 매핑
"""
import os
import time
import xml.etree.ElementTree as ET
import requests
import urllib3
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── .env 로딩 (dotenv 없을 때 직접 파싱으로 폴백) ──────────────────────────
def _load_env_file():
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env", override=False)
except ImportError:
    pass
_load_env_file()   # dotenv 없어도 환경변수 적재

_DATA_DIR = Path(__file__).parent.parent / "data"
_INCIDENTS_CSV = _DATA_DIR / "incidents_sample.csv"
_ACCIDENTS_CSV = _DATA_DIR / "accidents_history.csv"
_WEATHER_CSV   = _DATA_DIR / "weather_history.csv"

API_KEY     = os.getenv("API_KEY", "")
MAX_RETRIES = 3

# API 호출 결과를 사이드바 표시용으로 저장
_API_STATUS: dict = {"ok": False, "source": "unknown", "error": ""}

ITS_ERROR_CODES = {
    "4001": "서비스 미구독 — openapi.its.go.kr 로그인 후 trafficInfo 서비스 신청 필요",
    "4002": "요청 한도 초과",
    "4003": "서비스 점검 중",
    "4004": "잘못된 API URL",
    "4005": "서비스 미구독 — ITS Korea 포털에서 trafficInfo 신청 필요",
    "4006": "만료된 API 키",
}

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


def _parse_its_error(text: str) -> str:
    """ITS Korea XML 오류 응답에서 resultCode→한국어 메시지 추출."""
    try:
        root = ET.fromstring(text)
        code = root.findtext("header/resultCode", "")
        return ITS_ERROR_CODES.get(code, f"오류코드 {code}")
    except Exception:
        return "응답 파싱 실패"


def _fetch_its_api(rows=100):
    """재시도 3회, timeout 8s, SSL우회로 국토교통부 ITS 돌발상황 API 호출."""
    global _API_STATUS
    if not API_KEY:
        _API_STATUS = {"ok": False, "source": "no_key", "error": "API_KEY 없음 (.env 확인)"}
        return None

    url = (
        "https://openapi.its.go.kr:9443/trafficInfo"
        f"?apiKey={API_KEY}&type=json&numOfRows={rows}&pageNo=1"
    )
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=8, verify=False)

            # JSON 응답 처리
            if "application/json" in resp.headers.get("Content-Type", ""):
                data  = resp.json()
                items = data.get("body", {}).get("items", {}).get("item", [])
                if isinstance(items, dict):   # 단일 건이면 리스트로 감싸기
                    items = [items]
                if not items:
                    last_err = "응답 데이터 없음"
                    break
                df = pd.DataFrame(items)
                df = df.rename(columns={
                    "eventType":    "사고유형",
                    "roadName":     "노선명",
                    "occurTime":    "공지일시",
                    "laneCount":    "통제차로수",
                    "eventContent": "돌발내용",
                    "lat":          "위도",
                    "lng":          "경도",
                })
                _API_STATUS = {"ok": True, "source": "api", "error": ""}
                return df

            # XML 오류 응답 처리 (401 등)
            if resp.status_code != 200 or "<response>" in resp.text:
                last_err = _parse_its_error(resp.text)
                break

        except requests.exceptions.Timeout:
            last_err = f"타임아웃 (시도 {attempt+1}/{MAX_RETRIES})"
        except requests.exceptions.ConnectionError:
            last_err = "연결 실패"
        except Exception as exc:
            last_err = str(exc)

        if attempt < MAX_RETRIES - 1:
            time.sleep(1)

    _API_STATUS = {"ok": False, "source": "api_error", "error": last_err}
    return None


def fill_missing_incidents(df):
    """돌발상황 결측치 처리: 통제차로수→0, 기상상태→맑음, 지속시간→중앙값."""
    df = df.copy()
    if "통제차로수" in df.columns:
        df["통제차로수"] = pd.to_numeric(df["통제차로수"], errors="coerce").fillna(0)
    if "기상상태" in df.columns:
        df["기상상태"] = df["기상상태"].fillna("맑음")
    if "지속시간_분" in df.columns:
        median_dur = df["지속시간_분"].median()
        df["지속시간_분"] = df["지속시간_분"].fillna(median_dur)
    return df


def align_weather_to_incident(incident_df, weather_df):
    """각 돌발상황 발생 시각에 가장 근접한 ASOS 관측 레코드를 merge_asof로 매핑한다.

    시간 단위 불일치로 인한 대규모 결측을 방지하기 위해 nearest 전략 사용.
    매핑 허용 창(tolerance) = 90분; 초과 시 NaN 유지.
    """
    if incident_df.empty or weather_df.empty:
        return incident_df
    if "공지일시" not in incident_df.columns or "일시" not in weather_df.columns:
        return incident_df

    inc = incident_df.copy()
    wx  = weather_df.copy()
    inc["공지일시"] = pd.to_datetime(inc["공지일시"])
    wx["일시"]     = pd.to_datetime(wx["일시"])

    inc_sorted = inc.sort_values("공지일시")
    wx_sorted  = wx.sort_values("일시")

    wx_cols = ["기온_℃", "강수량_mm", "적설량_cm", "시정_km", "풍속_m/s", "습도_%"]
    wx_subset = wx_sorted[["일시"] + [c for c in wx_cols if c in wx_sorted.columns]]

    merged = pd.merge_asof(
        inc_sorted.reset_index(),
        wx_subset,
        left_on="공지일시",
        right_on="일시",
        direction="nearest",
        tolerance=pd.Timedelta("90min"),
    )
    merged = merged.set_index("index").reindex(inc.index)
    for col in wx_cols:
        if col in merged.columns:
            inc[col] = merged[col].values
    return inc


def _load_local_csv():
    if _INCIDENTS_CSV.exists():
        df = pd.read_csv(_INCIDENTS_CSV, encoding="utf-8-sig", parse_dates=["공지일시"])
        if len(df) > 10:
            return fill_missing_incidents(df)
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


def _compute_mixed_risk_label(controlled_lanes, weather_w, base_risk, hist_risk):
    """혼합 방식 위험 등급 산정.

    과거 사고 이력 기반 노선 위험도(hist_risk)와 실시간 요인
    (통제차로수 × 기상가중치)을 6:4 가중 결합한다.
    """
    realtime_score = controlled_lanes * weather_w * base_risk
    score = 0.6 * hist_risk + 0.4 * realtime_score
    bins = [-0.001, 0.35, 0.65, 10]
    labels = [0, 1, 2]
    return pd.cut(pd.Series(score), bins=bins, labels=labels).astype(int)


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

    # 과거 사고 이력에서 산정한 노선별 위험도(시뮬레이션 대체값)
    hist_risks = base_risks  # 실데이터에서는 load_accidents_history() 로 대체
    risk_level = _compute_mixed_risk_label(controlled_lanes, weather_w, base_risks, hist_risks)

    # 실시간 점수도 저장 (EDA용)
    risk_score = controlled_lanes * weather_w * base_risks

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
        if snow[i] > 0:           weather_cond.append("눈")
        elif vis[i] < 1.0:        weather_cond.append("안개")
        elif precip[i] > 0:       weather_cond.append("비")
        elif rng.random() < 0.3:  weather_cond.append("흐림")
        else:                     weather_cond.append("맑음")

    dates = pd.to_datetime({
        "year": 2024, "month": months, "day": days, "hour": hours, "minute": 0
    })
    return pd.DataFrame({
        "일시":       dates,
        "지점명":     rng.choice(stations, n),
        "기온_℃":    temp.round(1),
        "강수량_mm":  precip.round(1),
        "적설량_cm":  snow.round(1),
        "시정_km":    vis.round(2),
        "풍속_m/s":   rng.exponential(3, n).round(1),
        "습도_%":     rng.uniform(30, 100, n).round(0),
        "기상상태":   weather_cond,
    }).sort_values("일시").reset_index(drop=True)


@st.cache_data(ttl="1h", show_spinner=False)
def load_incidents(n=800, key_hint: str = ""):
    # key_hint 는 캐시 키에 포함 — API 키가 바뀌면 캐시 자동 무효화
    global _API_STATUS
    df = _fetch_its_api(n)
    if df is not None and len(df) > 10:
        _API_STATUS = {"ok": True, "source": "api", "error": ""}
        return fill_missing_incidents(df), "api"
    df = _load_local_csv()
    if df is not None:
        if _API_STATUS["source"] == "unknown":
            _API_STATUS = {"ok": False, "source": "no_key", "error": "API_KEY 없음"}
        return df, "csv"
    _API_STATUS.setdefault("source", "simulation")
    df = _generate_incidents(n)
    _DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(_INCIDENTS_CSV, index=False, encoding="utf-8-sig")
    return df, "simulation"


def get_api_status() -> dict:
    """사이드바 표시용 API 연결 상태 반환."""
    return _API_STATUS.copy()


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
