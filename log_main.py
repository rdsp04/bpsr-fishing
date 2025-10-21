import json
from datetime import datetime
from collections import defaultdict

FILENAME = "fishing_log.json"

def load_logs(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"No file named {filename} found.")
        return []
    except json.JSONDecodeError:
        print(f"File {filename} is not a valid JSON.")
        return []

def summarize_logs(logs):
    # Structure: summary[date][hour] = {"catch": n, "fail": n, "times": []}
    summary = defaultdict(lambda: defaultdict(lambda: {"catch": 0, "fail": 0, "times": []}))

    for entry in logs:
        ts = entry.get("timestamp")
        status = entry.get("catch")
        if ts is None or status is None:
            continue
        dt = datetime.fromisoformat(ts)
        date_str = dt.date().isoformat()
        hour_str = f"{dt.hour:02d}:00"

        summary[date_str][hour_str]["times"].append(dt)

        if status:
            summary[date_str][hour_str]["catch"] += 1
        else:
            summary[date_str][hour_str]["fail"] += 1

    return summary

def calculate_fish_per_minute(times):
    if len(times) < 2:
        return 0
    start = min(times)
    end = max(times)
    total_minutes =  60
    if total_minutes == 0:
        return len(times)
    return len(times) / total_minutes

def print_summary(summary):
    for date, hours in sorted(summary.items()):
        print(f"\nDate: {date}")
        for hour, counts in sorted(hours.items()):
            fpm = calculate_fish_per_minute(counts["times"])
            print(f"  Hour {hour} -> Caught: {counts['catch']}, Missed: {counts['fail']}, Fish/Min: {fpm:.2f}")

if __name__ == "__main__":
    logs = load_logs(FILENAME)
    if logs:
        summary = summarize_logs(logs)
        print_summary(summary)
    else:
        print("No logs to display.")
