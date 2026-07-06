import json
import os

for f in sorted(os.listdir("data")):
    if not f.endswith(".json"):
        continue
    with open(os.path.join("data", f), encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        dates = [r.get("date") or r.get("record_date") or "" for r in data]
        dates = [d for d in dates if d]
        if dates:
            print(f"{f}: {len(data)} records, {dates[0]} ~ {dates[-1]}")
        else:
            print(f"{f}: {len(data)} records, no dates")
    elif isinstance(data, dict):
        print(f"{f}: dict with keys {list(data.keys())}")
    else:
        print(f"{f}: {type(data).__name__}")
