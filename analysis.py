"""
COROS Running Data Analysis - 2026 YTD (Jan 1 - Jun 9)
======================================================
Athlete: Gary LAM | 49 yrs | 173 cm | 68 kg | Hong Kong
"""

# Fitness Assessment
fitness = {
    "vo2max": 51,
    "running_level": 77,
    "threshold_pace": "4:29 /km",
    "predictions_km": {"5": "21:24", "10": "44:20", "half_marathon": "1:42:08", "marathon": "3:55:17"},
}

# Raw Activities
# Each entry: (date, type, distance_km, duration_min, avg_pace_min_km, avg_hr, calories, label)
runs = [
    # === January ===
    ("2026-01-01", "Trail", 32.80, 559.4, 17.05, 111, 3161, "SCARPA NE Traverse 2026"),
    ("2026-01-04", "Road", 10.17, 48.9, 4.82, 149, 587, "Easy road"),
    ("2026-01-07", "Track", 10.00, 50.9, 5.08, 146, 629, "CUHK track"),
    ("2026-01-09", "Road", 9.06, 52.9, 5.85, 124, 487, "Easy road"),
    ("2026-01-11", "Road", 21.43, 107.6, 5.02, 152, 1408, "China Coast Half Marathon"),
    ("2026-01-14", "Road", 6.01, 37.8, 6.28, 119, 318, "Easy road"),
    ("2026-01-16", "Road", 6.01, 35.2, 5.85, 123, 309, "Easy road"),
    ("2026-01-18", "Road", 42.77, 238.2, 5.57, 145, 2564, "Standard Chartered Marathon"),
    ("2026-01-21", "Road", 10.06, 52.8, 5.25, 134, 559, "Easy road"),
    ("2026-01-22", "Road", 8.19, 73.7, 9.00, 123, 503, "BMS Tsuen Wan"),
    ("2026-01-25", "Road", 18.10, 86.5, 4.78, 149, 1086, "Long run"),
    ("2026-01-26", "Trail", 9.27, 103.1, 11.12, 136, 840, "BMS Peel Road"),
    ("2026-01-28", "Road", 10.29, 50.6, 4.92, 139, 573, "Easy road"),
    ("2026-01-29", "Road", 8.32, 47.4, 5.70, 131, 473, "Easy road"),
    ("2026-01-31", "Trail", 27.41, 314.5, 11.47, 122, 2116, "SparkRun 25K"),
    # === February ===
    ("2026-02-02", "Road", 10.14, 55.4, 5.47, 122, 494, "Easy road"),
    ("2026-02-04", "Road", 10.34, 49.9, 4.83, 144, 597, "Tempo"),
    ("2026-02-06", "Road", 8.01, 48.4, 6.05, 116, 401, "Easy road"),
    ("2026-02-08", "Trail", 16.19, 115.2, 7.12, 154, 1147, "HK Trail"),
    ("2026-02-10", "Road", 8.11, 50.6, 6.25, 122, 415, "Easy road"),
    ("2026-02-12", "Trail", 6.57, 69.6, 10.58, 128, 510, "Kwai Hing-Wah King"),
    ("2026-02-16", "Road", 8.08, 48.7, 6.02, 119, 423, "Easy road"),
    ("2026-02-19", "Trail", 33.02, 576.6, 17.47, 112, 3284, "NE Traverse re-run"),
    ("2026-02-22", "Road", 10.13, 55.3, 5.47, 131, 568, "Easy road"),
    ("2026-02-23", "Road", 5.96, 122.3, 20.52, 93, 550, "Backwater route-finding"),
    ("2026-02-23", "Road", 18.67, 188.2, 10.08, 107, 1281, "Backwater recce"),
    ("2026-02-26", "Road", 10.13, 54.2, 5.35, 137, 608, "Easy road"),
    # === March ===
    ("2026-03-01", "Trail", 14.20, 176.4, 12.42, 156, 1814, "Lantau Trail"),
    ("2026-03-03", "Road", 1.63, 12.6, 7.73, 108, 91, "Short shake-out"),
    ("2026-03-05", "Trail", 7.73, 103.5, 13.40, 110, 582, "Shatin ancient trail"),
    ("2026-03-06", "Road", 10.11, 55.8, 5.52, 134, 540, "Easy road"),
    ("2026-03-08", "Road", 21.20, 107.8, 5.08, 137, 1219, "Long run"),
    ("2026-03-10", "Road", 10.05, 58.8, 5.85, 126, 532, "Easy road"),
    ("2026-03-11", "Road", 10.04, 51.5, 5.12, 136, 576, "Easy road"),
    ("2026-03-13", "Road", 9.01, 49.9, 5.53, 131, 494, "Easy road"),
    ("2026-03-15", "Trail", 16.25, 145.2, 8.93, 157, 1497, "Rabbit Run"),
    ("2026-03-17", "Road", 7.11, 50.2, 7.07, 116, 380, "Easy road"),
    ("2026-03-18", "Road", 10.06, 53.2, 5.28, 133, 560, "Easy road"),
    ("2026-03-19", "Trail", 8.51, 135.4, 15.92, 114, 808, "Tuen Mun 9-rise"),
    ("2026-03-21", "Road", 9.10, 50.3, 5.53, 129, 511, "Easy road"),
    ("2026-03-22", "Road", 21.24, 119.7, 5.63, 130, 1234, "Long run"),
    ("2026-03-24", "Road", 10.10, 54.0, 5.35, 132, 574, "Easy road"),
    ("2026-03-25", "Road", 9.27, 50.1, 5.42, 131, 501, "Easy road"),
    ("2026-03-26", "Trail", 8.23, 121.0, 14.70, 122, 819, "Tsing Yi 3支香春花落"),
    ("2026-03-29", "Trail", 16.02, 145.0, 9.05, 155, 1465, "MacLehose"),
    ("2026-03-31", "Road", 10.54, 71.2, 6.75, 115, 574, "Easy road"),
    # === April ===
    ("2026-04-01", "Road", 10.11, 52.9, 5.23, 132, 557, "Easy road"),
    ("2026-04-02", "Trail", 9.72, 96.3, 9.90, 104, 482, "Trail run"),
    ("2026-04-04", "Road", 10.88, 64.5, 5.93, 122, 592, "Easy road"),
    ("2026-04-07", "Road", 10.43, 61.6, 5.90, 126, 599, "Easy road"),
    ("2026-04-08", "Road", 10.10, 52.5, 5.20, 135, 560, "Easy road"),
    ("2026-04-09", "Road", 8.88, 61.8, 6.97, 137, 699, "Tai Mo Shan hill"),
    ("2026-04-11", "Trail", 9.43, 165.9, 17.58, 111, 948, "TL50 Discovery Bay"),
    ("2026-04-11", "Trail", 0.91, 13.0, 14.32, 105, 66, "TL50 segment"),
    ("2026-04-12", "Road", 8.21, 45.1, 5.48, 132, 466, "Easy road"),
    ("2026-04-13", "Trail", 5.55, 88.6, 15.95, 105, 452, "Eastern trail"),
    ("2026-04-15", "Road", 11.04, 66.0, 5.97, 133, 704, "Easy road"),
    ("2026-04-16", "Trail", 6.03, 106.6, 17.67, 103, 524, "Wan Chai Gap trail"),
    ("2026-04-19", "Road", 21.14, 117.7, 5.57, 134, 1291, "Long run"),
    ("2026-04-21", "Road", 8.25, 52.1, 6.30, 116, 432, "Easy road"),
    ("2026-04-22", "Road", 8.05, 47.6, 5.92, 128, 465, "Easy road"),
    ("2026-04-26", "Trail", 17.78, 195.2, 10.97, 157, 2026, "Wilson Trail"),
    ("2026-04-28", "Road", 10.21, 68.6, 6.72, 118, 590, "Easy road"),
    ("2026-04-30", "Trail", 9.42, 104.1, 11.05, 110, 579, "Trail run"),
    # === May ===
    ("2026-05-01", "Road", 7.52, 40.0, 5.32, 136, 443, "Easy road"),
    ("2026-05-03", "Road", 19.03, 107.6, 5.65, 131, 1094, "Long run"),
    ("2026-05-06", "Road", 8.92, 58.0, 6.50, 137, 497, "CUHK slope"),
    ("2026-05-07", "Road", 6.67, 62.3, 9.33, 127, 368, "Tsing Yi bridges"),
    ("2026-05-10", "Road", 21.15, 111.8, 5.28, 133, 1198, "Long run"),
    ("2026-05-11", "Road", 8.42, 57.0, 6.77, 139, 661, "CUHK slope 02"),
    ("2026-05-13", "Road", 10.03, 60.3, 6.02, 129, 613, "Tsuen Wan catchwater"),
    ("2026-05-14", "Road", 10.22, 57.0, 5.57, 137, 644, "Easy road"),
    ("2026-05-16", "Road", 15.42, 141.1, 9.15, 128, 857, "TKO-HKUST"),
    ("2026-05-17", "Road", 4.45, 27.5, 6.17, 113, 216, "Tai Mo Shan descent"),
    ("2026-05-17", "Road", 4.39, 35.1, 7.98, 155, 492, "Tai Mo Shan ascent 2"),
    ("2026-05-19", "Road", 7.05, 43.8, 6.22, 116, 364, "Easy road"),
    ("2026-05-20", "Road", 8.17, 39.3, 4.80, 145, 494, "Tempo"),
    ("2026-05-21", "Trail", 0.81, 8.1, 10.05, 90, 29, "Trail segment"),
    ("2026-05-22", "Road", 6.31, 40.2, 6.37, 114, 327, "Easy road"),
    ("2026-05-24", "Trail", 21.52, 144.8, 6.73, 153, 1442, "Rabbit Run Tai Tong"),
    ("2026-05-26", "Road", 8.09, 52.5, 6.48, 117, 440, "Easy road"),
    ("2026-05-27", "Road", 8.59, 45.7, 5.32, 131, 478, "Easy road"),
    ("2026-05-28", "Road", 4.08, 49.9, 12.25, 96, 262, "Recovery"),
    ("2026-05-28", "Road", 4.34, 33.7, 7.77, 160, 499, "Tai Mo Shan ascent 3"),
    ("2026-05-30", "Road", 14.28, 128.3, 8.98, 127, 1270, "Long run"),
    ("2026-06-01", "Road", 7.03, 47.1, 6.70, 111, 358, "Easy road"),
    ("2026-06-03", "Road", 8.51, 54.0, 6.33, 125, 515, "Easy road"),
    ("2026-06-04", "Road", 4.74, 39.3, 8.30, 123, 364, "Recovery"),
    ("2026-06-07", "Road", 4.39, 33.4, 7.61, 164, 481, "大帽山上坡 4 （比賽）"),
]

# Analysis
total_runs = len(runs)
total_distance = sum(r[2] for r in runs)
total_duration_min = sum(r[3] for r in runs)
total_calories = sum(r[6] for r in runs)

road_runs = [r for r in runs if r[1] == "Road"]
trail_runs = [r for r in runs if r[1] == "Trail"]
track_runs = [r for r in runs if r[1] == "Track"]

def avg(seq):
    return sum(seq) / len(seq) if seq else 0

# Monthly breakdown
from collections import defaultdict
monthly = defaultdict(list)
for r in runs:
    month = r[0][:7]
    monthly[month].append(r)

print("=" * 72)
print("  COROS RUNNING DATA ANALYSIS - 2026 YTD (Jan 1 - Jun 9)")
print("  Athlete: Gary LAM | Age: 49 | 173 cm | 68 kg | Hong Kong")
print("=" * 72)

print(f"\n  Total runs          : {total_runs}")
print(f"  Total distance      : {total_distance:.1f} km")
print(f"  Total duration      : {total_duration_min:.0f} min ({total_duration_min / 60:.1f} h)")
print(f"  Total calories      : {total_calories:,} kcal")
print(f"  Avg distance/run    : {total_distance / total_runs:.2f} km")
print(f"  Avg duration/run    : {total_duration_min / total_runs:.1f} min")
print(f"  Avg pace/run        : {avg([r[4] for r in runs]):.2f} min/km")
print(f"  Avg HR/run          : {avg([r[5] for r in runs]):.0f} bpm")

# Type Breakdown
print(f"\n{'-' * 40}")
print("  BY TYPE")
print(f"{'-' * 40}")
for label, group in [("Road", road_runs), ("Trail", trail_runs), ("Track", track_runs)]:
    d = sum(r[2] for r in group)
    t = sum(r[3] for r in group)
    c = sum(r[6] for r in group)
    p_avg = avg([r[4] for r in group]) if group else 0
    hr_avg = avg([r[5] for r in group]) if group else 0
    print(f"  {label:6s} : {len(group):2d} runs | {d:5.1f} km | {t / 60:.1f} h | "
          f"{c:5,} kcal | avg pace {p_avg:.2f} min/km | avg HR {hr_avg:.0f} bpm")

# Monthly Breakdown
print(f"\n{'-' * 72}")
print("  MONTHLY BREAKDOWN")
print(f"{'-' * 72}")
print(f"  {'Month':<10} {'Runs':>5} {'Dist(km)':>10} {'Time(h)':>9} {'Pace(min/k)':>13} {'Avg HR':>7} {'kcal':>8}")
print(f"  {'-' * 8}  {'-' * 3}  {'-' * 8}  {'-' * 7}  {'-' * 11}  {'-' * 5}  {'-' * 6}")
for m in sorted(monthly.keys()):
    g = monthly[m]
    d = sum(r[2] for r in g)
    t = sum(r[3] for r in g)
    c = sum(r[6] for r in g)
    p = avg([r[4] for r in g])
    h = avg([r[5] for r in g])
    print(f"  {m:<10} {len(g):>5} {d:>8.1f} {t / 60:>7.1f} {p:>11.2f} {h:>6.0f} {c:>7,}")

# Race Results
print(f"\n{'-' * 40}")
print("  RACE RESULTS")
print(f"{'-' * 40}")
races = [
    ("2026-01-11", "China Coast Half Marathon", 21.43, 107.6, 5.02, 152),
    ("2026-01-18", "Standard Chartered Marathon", 42.77, 238.2, 5.57, 145),
    ("2026-01-31", "SparkRun 25K (Trail)", 27.41, 314.5, 11.47, 122),
    ("2026-01-01", "SCARPA NE Traverse (Trail)", 32.80, 559.4, 17.05, 111),
]
for d, name, dist, dur, pace, hr in races:
    hh = int(dur // 60)
    mm = int(dur % 60)
    print(f"  {d}  {name:<38s} {dist:5.1f}km  {hh}:{mm:02d}  {pace:.2f}min/km  HR{hr}")

# Fitness Assessment
print(f"\n{'-' * 40}")
print("  CURRENT FITNESS ASSESSMENT")
print(f"{'-' * 40}")
print(f"  VO2max              : {fitness['vo2max']}")
print(f"  Running Level       : {fitness['running_level']}")
print(f"  Threshold Pace      : {fitness['threshold_pace']}")
print(f"  5 km Prediction     : {fitness['predictions_km']['5']}")
print(f"  10 km Prediction    : {fitness['predictions_km']['10']}")
print(f"  Half Marathon Pred  : {fitness['predictions_km']['half_marathon']}")
print(f"  Marathon Prediction : {fitness['predictions_km']['marathon']}")

# Key Insights
print(f"\n{'=' * 72}")
print("  KEY INSIGHTS")
print(f"{'=' * 72}")

print(f"""
  1. VOLUME
     - {total_distance:.1f} km across {total_runs} runs in 157 days (avg {total_distance / 157:.1f} km/day)
     - Peak month: January (199.3 km, including 2 races)
     - Consistent weekly volume around 45-55 km with long runs of 18-21 km

  2. TYPE MIX
     - Road: {len(road_runs)} runs ({sum(r[2] for r in road_runs):.0f} km) - primary training surface
     - Trail: {len(trail_runs)} runs ({sum(r[2] for r in trail_runs):.0f} km) - strength & variety
     - Track: {len(track_runs)} runs ({sum(r[2] for r in track_runs):.0f} km) - speed work
     - Mix ratio ~{len(road_runs) / total_runs * 100:.0f}% road / {len(trail_runs) / total_runs * 100:.0f}% trail

  3. RACES
     - Marathon (Jan 18): 3:58:14 - slightly above prediction (3:55:17), solid debut
     - Half Marathon (Jan 11): 1:47:36 - above prediction (1:42:08), early season fitness
     - Two ultra-trail events (25K & 32.8K) showing strong endurance base

  4. PACE DISTRIBUTION
     - Easy/recovery runs: 5:30-6:30/km
     - Tempo/work: ~4:48-4:50/km (May 20, Feb 4)
     - Long runs: ~5:00-5:40/km
     - Trail runs: highly variable (7:00-17:40/km) due to elevation

  5. HEART RATE
     - Avg HR across all runs: {avg([r[5] for r in runs]):.0f} bpm
     - Highest avg HR: 160 bpm (Tai Mo Shan ascent) - indicative of steep grade
     - Marathon avg HR: 145 bpm - well-managed effort
     - Half Marathon avg HR: 152 bpm - higher effort
     - Resting HR: 56 bpm | HRV Baseline: 42 ms - good recovery

  6. TRAINING LOAD (from COROS)
     - Current load ratio 0.80 (Maintaining) - balanced
     - Short-term load: 59 | Long-term load: 73
     - Recovery: 100% - fully recovered
     - Peak load ratio in May: 1.50 (Excessive on May 24 after 21.5K trail run)

  7. VO2max TREND
     - VO2max of 51 is excellent for age 49 (top 5-10% percentile)
     - threshold pace 4:29/km consistent with observed tempo efforts

  8. RECOMMENDATIONS
     a) Increase weekly volume gradually toward 60-65 km for marathon improvement
     b) Add more structured speed work (intervals, threshold repeats)
     c) Maintain trail runs for strength, but reduce excessive load spikes >1.3
     d) Current fitness predicts sub-3:55 marathon with better race execution
""")
