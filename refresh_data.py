"""
refresh_data.py — Refresh COROS data JSON files by calling the COROS Training Hub API.

Usage:
    Set COROS_EMAIL, COROS_PASSWORD, and COROS_REGION in .env (this dir) or env vars.

    # Fetch latest data (incremental, since last refresh)
    python refresh_data.py

    # Fetch/replace data for a specific month
    python refresh_data.py --month 2026-06

Works with: https://teamapi.coros.com (auto-detected base URL for your account)
"""

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "coros-chatbox" / "backend" / "data"
TOKEN_CACHE = Path.home() / ".coros_token_cache.json"
LAST_REFRESH_FILE = DATA_DIR / ".last_refresh.json"

# Known COROS API hosts to try
API_HOSTS = [
    "https://teamapi.coros.com",      # US — works for this user
    "https://teamcnapi.coros.com",    # Asia
    "https://teameuapi.coros.com",    # EU
]


def get_creds() -> tuple:
    email = os.environ.get("COROS_EMAIL")
    password = os.environ.get("COROS_PASSWORD")
    region = os.environ.get("COROS_REGION", "us").lower()
    if not email or not password:
        print("ERROR: Set COROS_EMAIL and COROS_PASSWORD in .env or env vars.")
        sys.exit(1)
    return email, password, region


def try_login(base: str, email: str, password: str) -> dict | None:
    pwd_hash = hashlib.md5(password.encode()).hexdigest().lower()
    try:
        resp = httpx.post(
            f"{base}/account/login",
            json={"account": email, "accountType": 2, "pwd": pwd_hash},
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        if body.get("result") != "0000":
            return None
        data = body["data"]
        return {
            "base": base,
            "access_token": data["accessToken"],
            "user_id": str(data.get("userId", "")),
            "profile": {
                "birthday": str(data.get("birthday", "")),
                "weight_kg": data.get("weight", 0),
                "height_cm": data.get("stature", data.get("height", 0)),
                "gender": "male" if data.get("sex") == 1 else "female" if data.get("sex") == 2 else "",
                "nickname": data.get("nickname", ""),
                "max_hr": data.get("maxHr", 0),
                "resting_hr": data.get("rhr", 0),
            },
        }
    except Exception:
        return None


def login() -> dict:
    email, password, region = get_creds()

    if TOKEN_CACHE.exists():
        try:
            cache = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
            if cache.get("email") == email:
                remaining = (datetime.fromisoformat(cache["expires_at"]) - datetime.now()).total_seconds() / 3600
                if remaining > 1:
                    # Verify cached token still works
                    h = {
                        "Content-Type": "application/json",
                        "accessToken": cache["access_token"],
                        "yfheader": json.dumps({"userId": cache["user_id"]}),
                    }
                    try:
                        r = httpx.get(
                            f"{cache['base']}/activity/query?size=1&pageNumber=1&startDay=20260101&endDay={datetime.now().strftime('%Y%m%d')}",
                            headers=h, timeout=15,
                        )
                        if r.json().get("result") == "0000":
                            print(f"  Using cached token ({remaining:.0f}h remaining)")
                            return cache
                        print(f"  Cached token stale (result={r.json().get('result')}), re-logging ...")
                    except Exception:
                        print(f"  Cached token verification failed, re-logging ...")
        except Exception:
            pass

    # Try each API host; prefer the one that works for data queries
    for base in API_HOSTS:
        print(f"  Trying {base} ...")
        auth = try_login(base, email, password)
        if auth:
            print(f"  Login OK on {base}")
            # Verify token works for data queries
            h = {
                "Content-Type": "application/json",
                "accessToken": auth["access_token"],
                "yfheader": json.dumps({"userId": auth["user_id"]}),
            }
            try:
                r = httpx.get(
                    f"{base}/activity/query?size=1&pageNumber=1&startDay=20260101&endDay={datetime.now().strftime('%Y%m%d')}",
                    headers=h, timeout=15,
                )
                if r.json().get("result") == "0000":
                    print(f"  Token verified on {base}")
                    auth["base"] = base
                    auth["email"] = email
                    auth["expires_at"] = (datetime.now() + timedelta(hours=23)).isoformat()
                    TOKEN_CACHE.write_text(json.dumps(auth, indent=2), encoding="utf-8")
                    return auth
                print(f"  Token rejected on {base}, trying next host ...")
            except Exception as e:
                print(f"  Error on {base}: {e}, trying next ...")

    print("ERROR: Could not log in or verify token on any host.")
    sys.exit(1)


def auth_headers(auth: dict) -> dict:
    return {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "accessToken": auth["access_token"],
        "yfheader": json.dumps({"userId": auth["user_id"]}),
    }


def api_get(auth: dict, path: str, params: dict = None) -> dict | None:
    url = f"{auth['base']}{path}"
    try:
        resp = httpx.get(url, headers=auth_headers(auth), params=params, timeout=30)
        if resp.status_code != 200:
            return None
        body = resp.json()
        return body if body.get("result") == "0000" else None
    except Exception:
        return None


def api_post(auth: dict, path: str, payload: dict = None) -> dict | None:
    url = f"{auth['base']}{path}"
    try:
        resp = httpx.post(url, headers=auth_headers(auth), json=payload, timeout=30)
        if resp.status_code != 200:
            return None
        body = resp.json()
        return body if body.get("result") == "0000" else None
    except Exception:
        return None


# --- Data fetching ---

def read_last_refresh() -> str | None:
    if LAST_REFRESH_FILE.exists():
        try:
            data = json.loads(LAST_REFRESH_FILE.read_text(encoding="utf-8"))
            return data.get("last_date")
        except Exception:
            return None
    return None


def write_last_refresh(date_str: str):
    LAST_REFRESH_FILE.write_text(
        json.dumps({"last_date": date_str, "updated_at": datetime.now().isoformat()}, indent=2),
        encoding="utf-8",
    )


def fetch_activities(auth: dict, days: int = 200, since_day: str | None = None, month: str | None = None) -> list:
    end = datetime.now(timezone.utc)
    if month:
        start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
        if start.month == 12:
            end = datetime(start.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end = datetime(start.year, start.month + 1, 1) - timedelta(seconds=1)
    elif since_day:
        start = datetime.strptime(since_day, "%Y-%m-%d") - timedelta(days=1)
    else:
        start = end - timedelta(days=days)
    start_day = start.strftime("%Y%m%d")
    end_day = end.strftime("%Y%m%d")

    all_items = []
    page = 1
    size = 100

    while True:
        data = api_get(auth, "/activity/query", {
            "size": size, "pageNumber": page,
            "startDay": start_day, "endDay": end_day,
        })
        if not data:
            break
        items = data.get("data", {}).get("dataList", [])
        if not items:
            break
        all_items.extend(items)
        if len(items) < size:
            break
        page += 1

    print(f"  Fetched {len(all_items)} activities ({start_day} ~ {end_day})")
    return all_items


def fetch_activity_detail(auth: dict, label_id: str, sport_type: int) -> dict | None:
    """Fetch full activity detail including lap splits."""
    url = f"{auth['base']}/activity/detail/query"
    try:
        resp = httpx.post(
            url,
            data={"labelId": label_id, "userId": auth["user_id"], "sportType": str(sport_type)},
            headers={
                "accessToken": auth["access_token"],
                "yfheader": json.dumps({"userId": auth["user_id"]}),
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        if body.get("result") != "0000":
            return None
        return body.get("data")
    except Exception:
        return None


def extract_lap_splits(detail: dict) -> list:
    """Extract per-km lap splits from activity detail."""
    laps = detail.get("lapList", [])
    # Use auto-laps (type: 2), which contain per-km or per-segment splits
    items = []
    for lap in laps:
        if lap.get("type") == 2:
            items = lap.get("lapItemList", [])
            break
    if not items:
        # Fallback: use workout segments (type: 10) if no auto-laps
        for lap in laps:
            if lap.get("type") == 10:
                items = lap.get("lapItemList", [])
                break
    splits = []
    for i, item in enumerate(items):
        dist_cm = item.get("distance", 0)
        dist_km = dist_cm / 100000
        pace_s = item.get("avgPace", 0)
        splits.append({
            "km": i + 1,
            "distance_km": round(dist_km, 2),
            "avg_pace_sec": pace_s,
            "avg_pace": f"{int(pace_s // 60)}:{int(pace_s % 60):02d}" if pace_s else "0:00",
            "avg_hr": item.get("avgHr", 0),
            "avg_cadence": item.get("avgCadence", 0),
            "altitude": item.get("altitude", 0),
            "avg_power": item.get("avgPower", 0),
        })
    return splits


def fetch_dashboard(auth: dict) -> dict | None:
    data = api_get(auth, "/dashboard/query")
    if data:
        print(f"  Dashboard data OK")
    else:
        print(f"  WARNING: Dashboard query failed")
    return data.get("data") if data else None


# --- Data conversion ---

SPORT_NAMES = {
    100: "Outdoor Run", 101: "Indoor Run", 102: "Trail Run", 103: "Track Run", 104: "Hike",
    200: "Outdoor Bike", 201: "Indoor Bike", 202: "E-Bike", 203: "Gravel Bike", 204: "Mountain Bike",
    300: "Pool Swim", 301: "Open Water Swim",
    400: "Gym Cardio", 401: "GPS Cardio", 402: "Strength",
    900: "Walk", 901: "Jump Rope", 902: "Stair Climbing", 903: "Elliptical", 904: "Yoga", 905: "Pilates",
}


def to_sport_records(activities: list) -> list:
    records = []
    for a in activities:
        date = _extract_date(a)
        dist = a.get("distance", 0)
        if isinstance(dist, (int, float)) and dist > 1000:
            dist = dist / 1000
        dur = a.get("totalTime", 0)
        pace_sec = (dur / dist) if dist > 0 else 0
        pace_str = f"{int(pace_sec // 60)}:{int(pace_sec % 60):02d}"

        elev_gain = a.get("ascent") or 0
        elev_loss = a.get("descent") or 0
        start_ts = a.get("startTime") or 0
        start_hour = None
        if start_ts:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            start_hour = datetime.fromtimestamp(start_ts if start_ts < 1000000000000 else start_ts / 1000, tz=ZoneInfo("Asia/Hong_Kong")).hour

        records.append({
            "date": date,
            "sport_type": SPORT_NAMES.get(a.get("sportType"), f"Sport_{a.get('sportType')}"),
            "sport_code": a.get("sportType", 0),
            "location": a.get("name", ""),
            "duration_min": round(dur / 60, 2) if dur else 0,
            "distance_km": round(float(dist), 2) if dist else 0,
            "avg_pace": pace_str,
            "avg_hr": a.get("avgHr") or 0,
            "max_hr": a.get("maxHr") or 0,
            "avg_cadence": a.get("avgCadence") or 0,
            "calories": round((a.get("calorie") or 0) / 1000),
            "elevation_gain_m": round(float(elev_gain), 1) if elev_gain else 0,
            "elevation_loss_m": round(float(elev_loss), 1) if elev_loss else 0,
            "start_time": start_ts,
            "start_hour": start_hour,
        })
    records.sort(key=lambda r: r["date"], reverse=True)
    return records


def to_hrv_records(dashboard: dict) -> list:
    hrv_data = dashboard.get("summaryInfo", {}).get("sleepHrvData", {})
    records = []
    for item in hrv_data.get("sleepHrvList", []):
        date = str(item.get("happenDay", ""))
        if date:
            records.append({
                "date": date[:10],
                "avg_hrv": item.get("avgSleepHrv"),
                "baseline": item.get("sleepHrvBase"),
                "sd": item.get("sleepHrvSd"),
            })
    records.sort(key=lambda r: r["date"], reverse=True)
    return records


def to_fitness_assessment(dashboard: dict) -> dict:
    s = dashboard.get("summaryInfo", {})
    return {
        "vo2max": 51,
        "running_level": s.get("staminaLevel"),
        "lthr": s.get("lthr"),
        "ltsp_pace_per_km": s.get("ltsp"),
        "stamina_level": s.get("staminaLevel"),
        "aerobic_endurance_score": s.get("aerobicEnduranceScore"),
        "anaerobic_endurance_score": s.get("anaerobicEnduranceScore"),
        "anaerobic_capacity_score": s.get("anaerobicCapacityScore"),
        "lactate_threshold_capacity_score": s.get("lactateThresholdCapacityScore"),
        "recovery_percent": s.get("recoveryPct"),
        "resting_hr": s.get("rhr"),
    }


def to_recovery(dashboard: dict) -> dict:
    s = dashboard.get("summaryInfo", {})
    recovery = s.get("recoveryPct", 0)
    level = (
        "Heavy training allowed" if recovery >= 90
        else "Moderate training" if recovery >= 70
        else "Light training"
    )
    return {
        "recovery_percent": recovery,
        "level": level,
        "estimated_full_recovery_hours": s.get("fullRecoveryHours", 0),
        "resting_hr": s.get("rhr"),
    }


def _extract_date(item: dict) -> str:
    ds = item.get("date") or item.get("startTime")
    if isinstance(ds, int):
        if ds > 1000000000000:
            return datetime.fromtimestamp(ds / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        elif ds > 20000000:
            s = str(ds)
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        elif ds > 1000000000:
            return datetime.fromtimestamp(ds, tz=timezone.utc).strftime("%Y-%m-%d")
    elif isinstance(ds, str) and ds:
        return ds[:10]
    return ""


def to_hr_data(activities: list) -> list:
    records = {}
    for a in activities:
        date = _extract_date(a)
        if not date:
            continue
        avg_hr = a.get("avgHr") or 0
        max_hr = a.get("maxHr") or 0
        if date not in records:
            records[date] = {"date": date, "avg_hrs": [], "max_hrs": []}
        if avg_hr:
            records[date]["avg_hrs"].append(int(avg_hr))
        if max_hr:
            records[date]["max_hrs"].append(int(max_hr))
    result = []
    for date, data in sorted(records.items(), reverse=True):
        result.append({
            "date": date,
            "avg_hr": int(sum(data["avg_hrs"]) / len(data["avg_hrs"])) if data["avg_hrs"] else 0,
            "max_hr": max(data["max_hrs"]) if data["max_hrs"] else 0,
        })
    return result


def save_json(filename: str, data):
    path = DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    count = len(data) if isinstance(data, list) else 1
    print(f"  Wrote {path.name} ({count} records)")


def load_existing(filename: str):
    path = DATA_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def main():
    parser = argparse.ArgumentParser(description="Refresh COROS data from Training Hub API")
    parser.add_argument("--month", type=str, help="Specific month to refresh (e.g. 2026-06)")
    args = parser.parse_args()

    print("COROS Data Refresh")
    if args.month:
        print(f"  Month: {args.month}")
    print("=" * 50)

    auth = login()

    if args.month:
        days = 200
        since_day = None
    else:
        last_date = read_last_refresh()
        if last_date:
            print(f"\nLast refresh was on {last_date}, fetching only newer data ...")
            days = 200
            since_day = last_date
        else:
            print("\nNo previous refresh found, fetching full history ...")
            days = 200
            since_day = None

    print("\nFetching activities ...")
    activities = fetch_activities(auth, days=days, since_day=since_day, month=args.month)
    if activities:
        records = to_sport_records(activities)
        print("\nFetching lap splits for running activities (parallel) ...")
        run_activities = [a for a in activities if a.get("sportType") in (100, 101, 102, 103)]
        n_fetched = 0
        max_workers = 8
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            fut_map = {}
            for a in run_activities:
                lid = a.get("labelId")
                if not lid:
                    continue
                fut = executor.submit(fetch_activity_detail, auth, lid, a["sportType"])
                fut_map[fut] = a
            for fut in as_completed(fut_map):
                a = fut_map[fut]
                try:
                    detail = fut.result()
                except Exception:
                    detail = None
                if detail:
                    splits = extract_lap_splits(detail)
                    date = _extract_date(a)
                    for rec in records:
                        if rec["date"] == date and rec["sport_code"] == a.get("sportType"):
                            rec["lap_splits"] = splits
                            break
                    n_fetched += 1
                if n_fetched % 20 == 0 and n_fetched > 0:
                    print(f"    ... {n_fetched} done")
        print(f"  Fetched lap splits for {n_fetched} activities")

        # Merge with existing data
        existing = load_existing("sport_records.json")
        if existing:
            if args.month:
                # Replace records within the specified month, keep everything else
                merged = records + [r for r in existing if not r["date"].startswith(args.month)]
                print(f"  Replaced data for {args.month}: {len(records)} records inserted")
            elif since_day:
                new_keys = {(r["date"], r["sport_code"]) for r in records}
                merged = records + [r for r in existing if (r["date"], r["sport_code"]) not in new_keys]
                n_new = len(records)
                print(f"  Merged: {len(existing)} existing + {n_new} new = {len(merged)} total")
            else:
                merged = records
            merged.sort(key=lambda r: r["date"], reverse=True)
            records = merged
        save_json("sport_records.json", records)

        hr = to_hr_data(activities)
        if hr:
            existing_hr = load_existing("avg_heart_rate.json")
            if existing_hr and since_day:
                new_hr_dates = {r["date"] for r in hr}
                merged_hr = hr + [r for r in existing_hr if r["date"] not in new_hr_dates]
                merged_hr.sort(key=lambda r: r["date"], reverse=True)
                hr = merged_hr
            save_json("avg_heart_rate.json", hr)

        # Update last refresh date
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        write_last_refresh(today)
        print(f"  Last refresh updated to {today}")
    else:
        print("  No new activities found.")
        if not since_day:
            print("  WARNING: No activities fetched at all. Check credentials / API availability.")

    print("\nFetching dashboard ...")
    dashboard = fetch_dashboard(auth)
    if dashboard:
        hrv = to_hrv_records(dashboard)
        if hrv:
            save_json("hrv_data.json", hrv)
        save_json("recovery.json", to_recovery(dashboard))
        save_json("fitness_assessment.json", to_fitness_assessment(dashboard))

    print("\nSaving user profile ...")
    if auth.get("profile"):
        save_json("user_profile.json", auth["profile"])

    print("\nDone.")


if __name__ == "__main__":
    main()
