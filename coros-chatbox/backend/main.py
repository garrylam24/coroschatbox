import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
import math
from io import BytesIO
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

load_dotenv()
# Also load root .env for COROS credentials
root_env = Path(__file__).parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(root_env)

DATA_DIR = Path(__file__).parent / "data"
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="COROS Chatbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")

uploaded_files = {}
conversations = {}
MAX_HISTORY_EXCHANGES = 10

class ChatRequest(BaseModel):
    message: str
    file_ids: list[str] = []
    session_id: str = ""
    mode: str = "auto"  # "auto" | "data" | "coach"

class ChatResponse(BaseModel):
    reply: str
    fetched_urls: list[str] = []
    session_id: str = ""
    mode: str = "auto"

def load_data():
    data = {}
    for f in DATA_DIR.glob("*.json"):
        with open(f, encoding="utf-8") as fh:
            data[f.stem] = json.load(fh)
    return data

PROMPT_DATA = """You are a fast data-retrieval assistant for Gary LAM's COROS data. You have a very specific personality: you are a **刻薄的體育教練 (mean sports coach)** — blunt, sarcastic, and brutally honest. You call Gary "Bro" or "細路" (kid). You mock him when the data is bad and give backhanded compliments when it's good. Keep responses short and sharp, like a coach yelling from the sideline.

You have THREE special abilities:
1. **Web access** — You can fetch any URL the user provides.
2. **Data analysis** — You can analyze uploaded GPX files and photos.
3. **Chart rendering** — You can generate charts using Mermaid syntax inside ```mermaid code blocks.

Here is the user's COROS data context:

## User Profile
{user_profile}

## Devices
{devices}

## Fitness Assessment
{fitness}

## Recovery Status
{recovery}

## Training Load (recent 30 days)
{training_load}

## Sport Records (2026 YTD)
{sport_records}

## Average Heart Rate (recent 90 days)
{avg_hr}

Always answer in Traditional Chinese (繁體中文).

Your role: just fetch and present the data the user asks for. Be short and factual. List the numbers and stop. Do NOT perform deep analysis, correlation, or training advice — refer to the coach mode if the user asks for deeper insight.

If you want to fetch a URL to get more information, tell the user to paste the URL and you'll analyze it.

When presenting data that would benefit from visualization, include a Mermaid xychart-beta chart (```mermaid block). Each chart element on its own line. Never include a `---config---` frontmatter block."""

PROMPT_COACH = """You are a senior running coach analyst for Gary LAM. You have a very specific personality: you are a **刻薄的體育教練 (mean sports coach)** — sarcastic, brutally honest, but your analysis is always spot-on. You call Gary "Bro" or "細路" (kid). You roast him when the numbers are bad ("HRV dropped again? You sleeping in a dumpster?"), but you also give genuine, hard-earned praise when he earns it. Your analysis is thorough, but delivered with attitude.

You have THREE special abilities:
1. **Web access** — You can fetch any URL the user provides.
2. **Data analysis** — You can analyze uploaded GPX files and photos.
3. **Chart rendering** — You can generate charts using Mermaid syntax inside ```mermaid code blocks.

Here is the user's COROS data context:

## User Profile
{user_profile}

## Devices
{devices}

## Fitness Assessment
{fitness}

## Recovery Status
{recovery}

## Training Load (recent 30 days)
{training_load}

## Sport Records (2026 YTD)
{sport_records}

## Average Heart Rate (recent 90 days)
{avg_hr}

Always answer in Traditional Chinese (繁體中文).

Your role: analyze patterns, correlate multiple data streams, diagnose training status, and give personalized recommendations. Look for:
- Load ratio (short-term / long-term): optimal 0.8–1.3
- HRV trend vs baseline: sustained drop >7 ms signals fatigue
- Resting HR trend: sustained elevation >3 bpm signals incomplete recovery
- Sleep trend: chronic <6h or decreasing deep sleep = recovery risk
- Training monotony: consistently same pace/distance = plateau risk

If you want to fetch a URL to get more information, tell the user to paste the URL and you'll analyze it.

Whenever you present data that would benefit from visualization (volume, pace trends, heart rate trends, training load comparison, race analysis, etc.), ALWAYS include a Mermaid xychart-beta chart in ```mermaid blocks. Each chart element (title, x-axis, y-axis, line, bar) MUST be on its own separate line — never commas between them. Never include a `---config---` frontmatter block.

Be thorough and analytical. Back up every claim with specific numbers. Proactive follow-up insights are encouraged."""

def build_context(mode: str = "auto"):
    data = load_data()
    up = data.get("user_profile", {})
    dv = data.get("devices", [])
    fa = data.get("fitness_assessment", {})
    rc = data.get("recovery", {})
    tl = data.get("training_load", [])
    sr = data.get("sport_records", [])
    hr = data.get("avg_heart_rate", [])

    user_profile = f"Name: {up.get('nickname','N/A')}, Age: {up.get('age','N/A')}, Gender: {up.get('gender','N/A')}, Height: {up.get('height_cm','N/A')}cm, Weight: {up.get('weight_kg','N/A')}kg"
    devices = f"Watch: {dv[0].get('model_name','N/A')} ({dv[0].get('device_id','N/A')})" if dv else "N/A"
    fitness = f"VO2max: {fa.get('vo2max','N/A')}, Running Level: {fa.get('running_level','N/A')}/100, Threshold Pace: {fa.get('threshold_pace','4:29 /km')}, Predictions: {json.dumps(fa.get('predictions',{}))}" if fa else "N/A"
    recovery = f"Recovery: {rc.get('recovery_percent','N/A')}%, Level: {rc.get('level','N/A')}" if rc else "N/A"

    tl_str = "\n".join([f"  {d['date']}: {d['comment']} (ST={d['short_term_load']}, LT={d['long_term_load']}, ratio={d['ratio']})" for d in tl[-30:]])
    sr_str = json.dumps(sr, indent=2, ensure_ascii=False)
    hr_str = json.dumps(hr[-30:], indent=2, ensure_ascii=False)[:3000]

    prompt_template = PROMPT_DATA if mode == "data" else PROMPT_COACH if mode == "coach" else PROMPT_COACH
    return prompt_template.format(
        user_profile=user_profile,
        devices=devices,
        fitness=fitness,
        recovery=recovery,
        training_load=tl_str,
        sport_records=sr_str,
        avg_hr=hr_str
    )

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def parse_gpx(content: bytes):
    root = ET.fromstring(content)
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
    tracks = []
    total_distance = 0
    total_ele_gain = 0
    total_ele_loss = 0
    point_count = 0
    start_time = None
    end_time = None
    min_lat = 90
    min_lon = 180
    max_lat = -90
    max_lon = -180
    time_series = {"distances": [], "elevations": [], "paces": [], "timestamps": []}
    seg_distance = 0
    for trk in root.findall(".//gpx:trk", ns):
        name = trk.findtext("gpx:name", "", ns)
        for seg in trk.findall("gpx:trkseg", ns):
            pts = seg.findall("gpx:trkpt", ns)
            prev = None
            for pt in pts:
                lat = float(pt.get("lat"))
                lon = float(pt.get("lon"))
                ele = pt.findtext("gpx:ele", None, ns)
                ele = float(ele) if ele else None
                t = pt.findtext("gpx:time", None, ns)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)
                if prev:
                    d = haversine(prev["lat"], prev["lon"], lat, lon)
                    total_distance += d
                    seg_distance += d
                    if ele is not None and prev["ele"] is not None:
                        diff = ele - prev["ele"]
                        if diff > 0:
                            total_ele_gain += diff
                        else:
                            total_ele_loss += abs(diff)
                if t:
                    dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    if start_time is None or dt < start_time:
                        start_time = dt
                    if end_time is None or dt > end_time:
                        end_time = dt
                prev = {"lat": lat, "lon": lon, "ele": ele}
                point_count += 1
            tracks.append({"name": name, "points": len(pts)})
    duration = None
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds()
    info = {
        "type": "gpx",
        "total_distance_km": round(total_distance / 1000, 2),
        "total_elevation_gain_m": round(total_ele_gain, 1),
        "total_elevation_loss_m": round(total_ele_loss, 1),
        "track_count": len(tracks),
        "track_names": [t["name"] for t in tracks if t["name"]],
        "point_count": point_count,
        "duration_sec": duration,
        "bounds": {
            "min_lat": round(min_lat, 6),
            "max_lat": round(max_lat, 6),
            "min_lon": round(min_lon, 6),
            "max_lon": round(max_lon, 6)
        }
    }
    return info


GPX_EXT_NS = {
    "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
    "gpxdata": "http://www.cluetrust.com/XML/GPXDATA/2005/11",
}

def _gpx_ext_hr(pt: ET.Element) -> int | None:
    ext = pt.find("gpx:extensions", {"gpx": "http://www.topografix.com/GPX/1/1"})
    if ext is None:
        return None
    for ns_prefix, ns_uri in GPX_EXT_NS.items():
        tpe = ext.find(f"{ns_prefix}:TrackPointExtension", {**{"gpx": "http://www.topografix.com/GPX/1/1"}, **GPX_EXT_NS})
        if tpe is not None:
            hr = tpe.findtext(f"{ns_prefix}:hr", None, GPX_EXT_NS)
            if hr:
                return int(hr)
        hr = ext.findtext(f"{ns_prefix}:hr", None, {**{"gpx": "http://www.topografix.com/GPX/1/1"}, **GPX_EXT_NS})
        if hr:
            return int(hr)
    return None


def _gpx_ext_cad(pt: ET.Element) -> int | None:
    ext = pt.find("gpx:extensions", {"gpx": "http://www.topografix.com/GPX/1/1"})
    if ext is None:
        return None
    for ns_prefix, ns_uri in GPX_EXT_NS.items():
        tpe = ext.find(f"{ns_prefix}:TrackPointExtension", {**{"gpx": "http://www.topografix.com/GPX/1/1"}, **GPX_EXT_NS})
        if tpe is not None:
            cad = tpe.findtext(f"{ns_prefix}:cad", None, GPX_EXT_NS)
            if cad:
                return int(cad)
        cad = ext.findtext(f"{ns_prefix}:cad", None, {**{"gpx": "http://www.topografix.com/GPX/1/1"}, **GPX_EXT_NS})
        if cad:
            return int(cad)
    return None


def compute_gpx_time_series(content: bytes) -> dict:
    root = ET.fromstring(content)
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
    prev = None
    cumulative = 0.0
    series_dist = []
    series_ele = []
    series_hr = []
    series_cad = []
    series_pace = []
    series_time = []
    seg_start_time = None
    seg_start_dist = 0.0
    for trk in root.findall(".//gpx:trk", ns):
        for seg in trk.findall("gpx:trkseg", ns):
            pts = seg.findall("gpx:trkpt", ns)
            prev = None
            for pt in pts:
                lat = float(pt.get("lat"))
                lon = float(pt.get("lon"))
                ele = pt.findtext("gpx:ele", None, ns)
                ele = float(ele) if ele else None
                t = pt.findtext("gpx:time", None, ns)
                dt = datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None
                hr = _gpx_ext_hr(pt)
                cad = _gpx_ext_cad(pt)
                if prev is None:
                    seg_start_time = dt
                    seg_start_dist = cumulative
                    prev = {"lat": lat, "lon": lon, "ele": ele, "t": dt}
                    continue
                d = haversine(prev["lat"], prev["lon"], lat, lon)
                cumulative += d
                if d > 0 and dt and prev["t"]:
                    dt_sec = (dt - prev["t"]).total_seconds()
                    pace_per_km = (dt_sec / 60) / (d / 1000) if dt_sec > 0 else 0
                else:
                    pace_per_km = 0
                series_dist.append(round(cumulative, 1))
                series_ele.append(round(ele, 1) if ele else None)
                series_hr.append(hr)
                series_cad.append(cad)
                series_pace.append(round(pace_per_km, 2) if pace_per_km else None)
                series_time.append(dt.isoformat() if dt else None)
                prev = {"lat": lat, "lon": lon, "ele": ele, "t": dt}
    return {
        "distances_m": series_dist,
        "elevations_m": series_ele,
        "heart_rates": series_hr,
        "cadences": series_cad,
        "paces_min_per_km": series_pace,
        "timestamps": series_time,
        "total_km": round(cumulative / 1000, 2) if cumulative else 0,
    }

# ── TCX Parsing ──────────────────────────────────────────────────
TCX_NS = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

def parse_tcx(content: bytes):
    root = ET.fromstring(content)
    total_distance = 0.0
    total_duration = 0.0
    total_calories = 0
    trackpoints = []
    laps = []
    start_time = None
    end_time = None
    min_lat, max_lat = 90.0, -90.0
    min_lon, max_lon = 180.0, -180.0

    for act in root.findall(".//tcx:Activity", TCX_NS):
        for lap in act.findall("tcx:Lap", TCX_NS):
            dur = float(lap.findtext("tcx:TotalTimeSeconds", "0", TCX_NS))
            dist = float(lap.findtext("tcx:DistanceMeters", "0", TCX_NS))
            cal = int(float(lap.findtext("tcx:Calories", "0", TCX_NS)))
            total_duration += dur
            total_distance += dist
            total_calories += cal
            lap_data = {"duration_sec": dur, "distance_m": dist, "calories": cal}
            intensity = lap.findtext("tcx:Intensity", "", TCX_NS)
            if intensity:
                lap_data["intensity"] = intensity
            laps.append(lap_data)

            for trkpt in lap.findall("tcx:Track/tcx:Trackpoint", TCX_NS):
                t = trkpt.findtext("tcx:Time", None, TCX_NS)
                lat = None
                lon = None
                pos = trkpt.find("tcx:Position", TCX_NS)
                if pos is not None:
                    lat = float(pos.findtext("tcx:LatitudeDegrees", "0", TCX_NS))
                    lon = float(pos.findtext("tcx:LongitudeDegrees", "0", TCX_NS))
                    min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)
                    min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
                alt = trkpt.findtext("tcx:AltitudeMeters", None, TCX_NS)
                alt = float(alt) if alt else None
                hr_el = trkpt.find("tcx:HeartRateBpm/tcx:Value", TCX_NS)
                hr = int(hr_el.text) if hr_el is not None else None
                cad = trkpt.findtext("tcx:Cadence", None, TCX_NS)
                cad = int(cad) if cad else None

                trackpoints.append({
                    "time": t, "lat": lat, "lon": lon, "alt": alt,
                    "hr": hr, "cadence": cad,
                })
                if t:
                    dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    if start_time is None or dt < start_time:
                        start_time = dt
                    if end_time is None or dt > end_time:
                        end_time = dt

    total_ele_gain = 0.0
    total_ele_loss = 0.0
    prev_alt = None
    for tp in trackpoints:
        if tp["alt"] is not None and prev_alt is not None:
            diff = tp["alt"] - prev_alt
            if diff > 0:
                total_ele_gain += diff
            else:
                total_ele_loss += abs(diff)
        prev_alt = tp["alt"] if tp["alt"] is not None else prev_alt

    duration_sec = None
    if start_time and end_time:
        duration_sec = (end_time - start_time).total_seconds()

    return {
        "type": "tcx",
        "total_distance_km": round(total_distance / 1000, 2) if total_distance else 0,
        "total_duration_sec": round(total_duration, 1) if total_duration else duration_sec,
        "total_calories": total_calories,
        "total_elevation_gain_m": round(total_ele_gain, 1),
        "total_elevation_loss_m": round(total_ele_loss, 1),
        "lap_count": len(laps),
        "point_count": len(trackpoints),
        "avg_hr": _avg_of([tp["hr"] for tp in trackpoints if tp["hr"] is not None]),
        "avg_cadence": _avg_of([tp["cadence"] for tp in trackpoints if tp["cadence"] is not None]),
        "start_time": start_time.isoformat() if start_time else None,
        "bounds": {
            "min_lat": round(min_lat, 6), "max_lat": round(max_lat, 6),
            "min_lon": round(min_lon, 6), "max_lon": round(max_lon, 6),
        } if min_lat < 91 else None,
    }


def compute_tcx_time_series(content: bytes) -> dict:
    root = ET.fromstring(content)
    cumulative = 0.0
    series_dist = []; series_ele = []; series_hr = []; series_cad = []; series_pace = []; series_time = []
    prev = None
    for act in root.findall(".//tcx:Activity", TCX_NS):
        for lap in act.findall("tcx:Lap", TCX_NS):
            for trkpt in lap.findall("tcx:Track/tcx:Trackpoint", TCX_NS):
                t = trkpt.findtext("tcx:Time", None, TCX_NS)
                alt = trkpt.findtext("tcx:AltitudeMeters", None, TCX_NS)
                alt_f = float(alt) if alt else None
                lat = None; lon = None
                pos = trkpt.find("tcx:Position", TCX_NS)
                if pos is not None:
                    lat = float(pos.findtext("tcx:LatitudeDegrees", "0", TCX_NS))
                    lon = float(pos.findtext("tcx:LongitudeDegrees", "0", TCX_NS))
                hr_el = trkpt.find("tcx:HeartRateBpm/tcx:Value", TCX_NS)
                hr = int(hr_el.text) if hr_el is not None else None
                cad = trkpt.findtext("tcx:Cadence", None, TCX_NS)
                cad = int(cad) if cad else None
                dt_obj = datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None

                if prev is not None and lat is not None and prev["lat"] is not None:
                    d = haversine(prev["lat"], prev["lon"], lat, lon)
                    cumulative += d
                    if dt_obj and prev["t"]:
                        dt_sec = (dt_obj - prev["t"]).total_seconds()
                        pace = (dt_sec / 60) / (d / 1000) if d > 0 and dt_sec > 0 else 0
                    else:
                        pace = 0
                    series_pace.append(round(pace, 2) if pace else None)
                else:
                    series_pace.append(None)
                series_dist.append(round(cumulative, 1))
                series_ele.append(round(alt_f, 1) if alt_f is not None else None)
                series_hr.append(hr)
                series_cad.append(cad)
                series_time.append(dt_obj.isoformat() if dt_obj else None)
                prev = {"lat": lat, "lon": lon, "t": dt_obj}
    return {
        "distances_m": series_dist, "elevations_m": series_ele,
        "heart_rates": series_hr, "cadences": series_cad,
        "paces_min_per_km": series_pace, "timestamps": series_time,
        "total_km": round(cumulative / 1000, 2),
    }


# ── FIT Parsing ──────────────────────────────────────────────────
def parse_fit(content: bytes):
    import fitparse
    fitfile = fitparse.FitFile(BytesIO(content))
    records = []
    sessions = []
    laps = []
    file_id = {}

    for msg in fitfile.messages:
        if msg.name == "file_id":
            file_id = {k: v for k, v in msg.get_values().items()}
        elif msg.name == "session":
            sessions.append({k: v for k, v in msg.get_values().items()})
        elif msg.name == "lap":
            laps.append({k: v for k, v in msg.get_values().items()})
        elif msg.name == "record":
            records.append({k: v for k, v in msg.get_values().items()})

    sport = sessions[0].get("sport", "unknown") if sessions else "unknown"
    start_ts = sessions[0].get("start_time") if sessions else None
    end_ts = sessions[0].get("timestamp") if sessions else None
    total_dist = sum(s.get("total_distance", 0) or 0 for s in sessions)
    total_dur = sum(s.get("total_timer_time", 0) or 0 for s in sessions)
    total_cal = sum(s.get("total_calories", 0) or 0 for s in sessions)
    total_ascent = sum(s.get("total_ascent", 0) or 0 for s in sessions)
    total_descent = sum(s.get("total_descent", 0) or 0 for s in sessions)
    avg_hr = sessions[0].get("avg_heart_rate") if sessions else None
    max_hr = sessions[0].get("max_heart_rate") if sessions else None
    avg_cad = sessions[0].get("avg_cadence") if sessions else None

    min_lat, max_lat = 90.0, -90.0
    min_lon, max_lon = 180.0, -180.0
    for rec in records:
        slat = rec.get("semicircles_position_lat")
        slon = rec.get("semicircles_position_long")
        if slat is not None and slon is not None:
            lat = slat * (180.0 / 2**31)
            lon = slon * (180.0 / 2**31)
            min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)

    return {
        "type": "fit",
        "sport": sport,
        "total_distance_km": round(total_dist, 2) if total_dist else 0,
        "total_duration_sec": round(total_dur, 1) if total_dur else 0,
        "total_calories": round(total_cal) if total_cal else 0,
        "total_elevation_gain_m": round(float(total_ascent), 1) if total_ascent else 0,
        "total_elevation_loss_m": round(float(total_descent), 1) if total_descent else 0,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "avg_cadence": avg_cad,
        "session_count": len(sessions),
        "lap_count": len(laps),
        "record_count": len(records),
        "start_time": start_ts.isoformat() if hasattr(start_ts, "isoformat") else str(start_ts) if start_ts else None,
        "device": file_id.get("manufacturer", "unknown"),
        "bounds": {
            "min_lat": round(min_lat, 6), "max_lat": round(max_lat, 6),
            "min_lon": round(min_lon, 6), "max_lon": round(max_lon, 6),
        } if min_lat < 91 else None,
    }


def compute_fit_time_series(content: bytes) -> dict:
    import fitparse
    fitfile = fitparse.FitFile(BytesIO(content))
    cumulative = 0.0
    series_dist = []; series_ele = []; series_hr = []; series_cad = []; series_speed = []; series_time = []
    prev_lat = None; prev_lon = None; prev_t = None

    for msg in fitfile.messages:
        if msg.name != "record":
            continue
        rec = {k: v for k, v in msg.get_values().items()}
        ts = rec.get("timestamp")
        slat = rec.get("semicircles_position_lat")
        slon = rec.get("semicircles_position_long")
        alt = rec.get("altitude")
        hr = rec.get("heart_rate")
        cad = rec.get("cadence")
        speed = rec.get("speed")

        lat = slat * (180.0 / 2**31) if slat is not None else None
        lon = slon * (180.0 / 2**31) if slon is not None else None

        if lat is not None and prev_lat is not None:
            d = haversine(prev_lat, prev_lon, lat, lon)
            cumulative += d

        prev_lat = lat; prev_lon = lon

        series_dist.append(round(cumulative, 1))
        series_ele.append(round(float(alt), 1) if alt is not None else None)
        series_hr.append(int(hr) if hr is not None else None)
        series_cad.append(int(cad) if cad is not None else None)
        series_speed.append(round(speed, 2) if speed else None)
        series_time.append(ts.isoformat() if hasattr(ts, "isoformat") else str(ts) if ts else None)
        prev_t = ts

    return {
        "distances_m": series_dist, "elevations_m": series_ele,
        "heart_rates": series_hr, "cadences": series_cad,
        "speeds_mps": series_speed, "timestamps": series_time,
        "total_km": round(cumulative / 1000, 2),
    }


def _avg_of(values):
    return round(sum(values) / len(values)) if values else None


async def fetch_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            text = resp.text
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            text = re.sub(r"\n\s*\n", "\n", text)
            return text[:8000]
        else:
            return resp.text[:8000]

def extract_urls(text: str) -> list[str]:
    return list(set(URL_PATTERN.findall(text)))

async def call_deepseek(messages: list, model: str = "deepseek-v4-flash", max_tokens: int = 8192, thinking: bool = False) -> str:
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    if thinking:
        body["thinking"] = {"type": "enabled"}
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json=body
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"DeepSeek API error: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"]

@app.get("/api/health")
def health():
    return {"status": "ok", "data_files": list(load_data().keys())}

@app.post("/api/refresh")
def refresh_data():
    import subprocess, sys
    script = Path(__file__).parent.parent.parent / "refresh_data.py"
    project_root = script.parent
    if not script.exists():
        raise HTTPException(status_code=500, detail=f"refresh_data.py not found at {script}")
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(project_root),
            env=os.environ
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Refresh timed out after 120s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = uuid.uuid4().hex[:12]
    content = await file.read()
    ext = Path(file.filename).suffix.lower()
    if ext == ".gpx":
        info = parse_gpx(content)
        info["file_id"] = file_id
        info["filename"] = file.filename
        uploaded_files[file_id] = info
        gpx_path = UPLOAD_DIR / f"{file_id}.gpx"
        gpx_path.write_bytes(content)
        dur = info["duration_sec"]
        dur_str = f"{int(dur//3600)}h {int((dur%3600)//60)}m" if dur else "N/A"
        summary = (
            f"GPX file: {file.filename}\n"
            f"Distance: {info['total_distance_km']} km\n"
            f"Elevation gain: {info['total_elevation_gain_m']}m / loss: {info['total_elevation_loss_m']}m\n"
            f"Duration: {dur_str}\n"
            f"Tracks: {info['track_count']}\n"
            f"Points: {info['point_count']}"
        )
        return {"file_id": file_id, "type": "gpx", "summary": summary, "data": info}
    elif ext == ".tcx":
        info = parse_tcx(content)
        info["file_id"] = file_id
        info["filename"] = file.filename
        uploaded_files[file_id] = info
        tcx_path = UPLOAD_DIR / f"{file_id}.tcx"
        tcx_path.write_bytes(content)
        dur = info.get("total_duration_sec")
        dur_str = f"{int(dur//3600)}h {int((dur%3600)//60)}m" if dur else "N/A"
        hr_str = f", Avg HR: {info['avg_hr']}" if info.get("avg_hr") else ""
        cad_str = f", Cadence: {info['avg_cadence']}" if info.get("avg_cadence") else ""
        summary = (
            f"TCX file: {file.filename}\n"
            f"Distance: {info['total_distance_km']} km\n"
            f"Elevation gain: {info['total_elevation_gain_m']}m / loss: {info['total_elevation_loss_m']}m\n"
            f"Duration: {dur_str}{hr_str}{cad_str}\n"
            f"Laps: {info['lap_count']}, Points: {info['point_count']}"
        )
        return {"file_id": file_id, "type": "tcx", "summary": summary, "data": info}
    elif ext == ".fit":
        info = parse_fit(content)
        info["file_id"] = file_id
        info["filename"] = file.filename
        uploaded_files[file_id] = info
        fit_path = UPLOAD_DIR / f"{file_id}.fit"
        fit_path.write_bytes(content)
        dur = info.get("total_duration_sec")
        dur_str = f"{int(dur//3600)}h {int((dur%3600)//60)}m" if dur else "N/A"
        hr_str = f", Avg HR: {info['avg_hr']}" if info.get("avg_hr") else ""
        cad_str = f", Cadence: {info['avg_cadence']}" if info.get("avg_cadence") else ""
        summary = (
            f"FIT file: {file.filename}\n"
            f"Sport: {info['sport']}\n"
            f"Distance: {info['total_distance_km']} km\n"
            f"Elevation gain: {info['total_elevation_gain_m']}m / loss: {info['total_elevation_loss_m']}m\n"
            f"Duration: {dur_str}{hr_str}{cad_str}\n"
            f"Records: {info['record_count']}"
        )
        return {"file_id": file_id, "type": "fit", "summary": summary, "data": info}
    elif ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        dest = UPLOAD_DIR / f"{file_id}{ext}"
        dest.write_bytes(content)
        info = {"file_id": file_id, "filename": file.filename, "type": "image", "path": str(dest)}
        uploaded_files[file_id] = info
        return {"file_id": file_id, "type": "image", "summary": f"Image uploaded: {file.filename} ({len(content)//1024} KB)"}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use .gpx, .tcx, .fit, .jpg, .png")

@app.get("/api/uploads/{file_id}")
def get_upload(file_id: str):
    info = uploaded_files.get(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="File not found")
    if info.get("type") == "image":
        return FileResponse(info["path"], media_type=f"image/{Path(info['path']).suffix[1:]}")
    return info

@app.get("/api/chart/gpx/{file_id}")
def chart_gpx(file_id: str):
    info = uploaded_files.get(file_id)
    if not info or info.get("type") != "gpx":
        raise HTTPException(status_code=404, detail="GPX file not found")
    path = UPLOAD_DIR / f"{file_id}.gpx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Raw GPX data not available")
    return compute_gpx_time_series(path.read_bytes())

@app.get("/api/chart/tcx/{file_id}")
def chart_tcx(file_id: str):
    info = uploaded_files.get(file_id)
    if not info or info.get("type") != "tcx":
        raise HTTPException(status_code=404, detail="TCX file not found")
    path = UPLOAD_DIR / f"{file_id}.tcx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Raw TCX data not available")
    return compute_tcx_time_series(path.read_bytes())

@app.get("/api/chart/fit/{file_id}")
def chart_fit(file_id: str):
    info = uploaded_files.get(file_id)
    if not info or info.get("type") != "fit":
        raise HTTPException(status_code=404, detail="FIT file not found")
    path = UPLOAD_DIR / f"{file_id}.fit"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Raw FIT data not available")
    return compute_fit_time_series(path.read_bytes())


@app.get("/api/chart/coros-summary")
def chart_coros_summary():
    data = load_data()
    sr = data.get("sport_records", [])
    hr = data.get("avg_heart_rate", [])
    tl = data.get("training_load", [])
    monthly = {}
    monthly_elev = {}
    for r in sr:
        m = r.get("date", "")[:7]
        if m:
            monthly[m] = monthly.get(m, 0) + r.get("distance_km", 0)
            monthly_elev[m] = monthly_elev.get(m, 0) + (r.get("elevation_gain_m") or 0)
    return {
        "monthly_volume": [{"month": k, "km": round(v, 1)} for k, v in sorted(monthly.items())],
        "monthly_elevation": [{"month": k, "gain_m": round(v, 0)} for k, v in sorted(monthly_elev.items())],
        "heart_rate": [{"date": r["date"], "avg_hr": r["avg_hr"]} for r in hr[-90:]],
        "training_load": [{"date": r["date"], "st": r.get("short_term_load"), "lt": r.get("long_term_load")} for r in tl[-60:]],
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set.")

    data_keywords = ["跑量", "里程", "sleep", "心率", "配速", "list", "fetch", "query", "data", "show", "查詢", "上週", "昨天", "今天", "我的數據", "get data", "volume", "mileage", "distance", "pace", "heart rate", "hr", "recovery", "record", "log"]
    coach_keywords = ["分析", "建議", "diagnose", "overtrain", "trend", "plan", "advice", "evaluate", "correlation", "pattern", "診斷", "趨勢", "計劃", "過度訓練", "suggestion", "improve", "should", "why", "compare", "forecast", "predict"]

    mode = req.mode
    if mode == "auto":
        msg_lower = req.message.lower()
        data_score = sum(1 for kw in data_keywords if kw in msg_lower)
        coach_score = sum(1 for kw in coach_keywords if kw in msg_lower)
        mode = "data" if data_score > coach_score else "coach"

    model = "deepseek-v4-pro" if mode == "coach" else "deepseek-v4-flash"
    thinking_mode = (mode == "coach")
    sid = req.session_id or uuid.uuid4().hex[:12]
    print(f"[chat] session={sid[:8]} mode={mode} model={model} thinking={thinking_mode} msg='{req.message[:60]}'", flush=True)
    if sid not in conversations:
        conversations[sid] = [{"role": "system", "content": build_context(mode)}]
    else:
        conversations[sid][0]["content"] = build_context(mode)

    file_context = ""
    for fid in req.file_ids:
        info = uploaded_files.get(fid)
        if info:
            if info["type"] == "gpx":
                file_context += f"\n[Uploaded GPX: {info['filename']}]\n"
                file_context += f"Distance: {info['total_distance_km']}km, "
                if info["duration_sec"]:
                    d = info["duration_sec"]
                    file_context += f"Duration: {int(d//3600)}h {int((d%3600)//60)}m, "
                file_context += f"Elevation gain: {info['total_elevation_gain_m']}m, loss: {info['total_elevation_loss_m']}m\n"
                file_context += f"Bounds: {info['bounds']}\n\n"
            elif info["type"] == "image":
                file_context += f"\n[Uploaded Image: {info['filename']}]\n"

    user_message = req.message
    urls = extract_urls(user_message)
    fetched = []

    for url in urls:
        try:
            content = await fetch_url(url)
            summary = content[:1500]
            fetched.append(url)
            user_message += f"\n\n[Fetched from {url}]\n{summary}\n[/Fetched]"
        except Exception as e:
            user_message += f"\n\n[Failed to fetch {url}: {str(e)}]"

    chart_keywords = ["chart", "圖表", "visualize", "plot", "graph", "trend", "volume", "跑量", "regression", "weekly"]
    wants_chart = any(kw in req.message.lower() for kw in chart_keywords)
    if wants_chart:
        user_message += "\n\n[IMPORTANT: You MUST include a valid Mermaid xychart-beta chart in your response. Use the format: ```mermaid\nxychart-beta\n  title \"...\"\n  x-axis [...]\n  y-axis \"...\" 0 --> N\n  line [...]\n```]"

    conversations[sid].append({"role": "user", "content": file_context + user_message})

    reply = await call_deepseek(conversations[sid], model=model, thinking=thinking_mode)

    if wants_chart and "```mermaid" not in reply:
        conversations[sid].append({"role": "user", "content": "Please regenerate your response but this time you MUST include a Mermaid xychart-beta chart. Wrap it in a ```mermaid code block. Each element on its own line."})
        reply = await call_deepseek(conversations[sid], model=model, thinking=thinking_mode)

    conversations[sid].append({"role": "assistant", "content": reply})

    if len(conversations[sid]) > 1 + MAX_HISTORY_EXCHANGES * 2:
        system = conversations[sid][0]
        recent = conversations[sid][-(MAX_HISTORY_EXCHANGES * 2):]
        conversations[sid] = [system] + recent

    return ChatResponse(reply=reply, fetched_urls=fetched, session_id=sid, mode=mode)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
