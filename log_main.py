import json
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate

FISH_FILE = "fishing_log.json"
BROKEN_FILE = "broken_rods.json"


def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No file named {filename} found.")
        return []
    except json.JSONDecodeError:
        print(f"File {filename} is not a valid JSON.")
        return []


def summarize_fishing(logs):
    summary = defaultdict(lambda: defaultdict(lambda: {
        "catch": 0,
        "fail": 0,
        "times": [],
        "fish_types": defaultdict(int)
    }))

    all_fish_types = set()

    for entry in logs:
        ts = entry.get("timestamp")
        status = entry.get("catch")
        fish_type = entry.get("fish_type", "undefined_type")

        if ts is None or status is None:
            continue

        dt = datetime.fromisoformat(ts)
        date_str = dt.date().isoformat()
        hour_str = f"{dt.hour:02d}:00"

        summary[date_str][hour_str]["times"].append(dt)

        if status:
            summary[date_str][hour_str]["catch"] += 1
            summary[date_str][hour_str]["fish_types"][fish_type] += 1
            all_fish_types.add(fish_type)
        else:
            summary[date_str][hour_str]["fail"] += 1

    return summary, sorted(all_fish_types)


def summarize_broken_rods(logs):
    summary = defaultdict(lambda: defaultdict(int))
    for entry in logs:
        ts = entry.get("timestamp")
        broken = entry.get("broken")
        if not ts or not broken:
            continue
        dt = datetime.fromisoformat(ts)
        date_str = dt.date().isoformat()
        hour_str = f"{dt.hour:02d}:00"
        summary[date_str][hour_str] += 1
    return summary


def calculate_fish_per_minute(times):
    if len(times) < 2:
        return 0
    total_minutes = 60
    return len(times) / total_minutes


def print_summary(fish_summary, broken_summary, fish_types):
    total_caught = 0
    total_failed = 0
    total_broken = 0
    total_fish_types = defaultdict(int)

    for date, hours in sorted(fish_summary.items()):
        print(f"\nDate: {date}")
        rows = []
        for hour, counts in sorted(hours.items()):
            broken = broken_summary[date][hour] if date in broken_summary else 0
            total_broken += broken

            total = counts["catch"] + counts["fail"]
            rate = (counts["catch"] / total * 100) if total else 0
            fpm = calculate_fish_per_minute(counts["times"])

            total_caught += counts["catch"]
            total_failed += counts["fail"]

            # Merge fish type totals
            for ftype, count in counts["fish_types"].items():
                total_fish_types[ftype] += count

            # Build row with all fish type counts
            type_counts = [counts["fish_types"].get(ft, 0) for ft in fish_types]

            rows.append([
                hour,
                counts["catch"],
                counts["fail"],
                broken,
                f"{rate:.2f}%",
                f"{fpm:.2f}",
                *type_counts
            ])

        headers = ["Hour", "Caught", "Missed", "Broken Rods", "Catch Rate", "Fish/Min"] + fish_types
        print(tabulate(rows, headers=headers, tablefmt="simple"))

    total_fish = total_caught + total_failed
    total_rate = (total_caught / total_fish * 100) if total_fish else 0

    print("\nTOTAL STATISTICS")
    print(tabulate(
        [[
            total_caught,
            total_failed,
            total_broken,
            f"{total_rate:.2f}%",
            f"{total_caught / 60:.2f}"
        ]],
        headers=["Total Caught", "Total Missed", "Total Broken Rods", "Overall Catch Rate", "Avg Fish/Min"],
        tablefmt="simple",
    ))

    print("\nTOTAL FISH TYPES")
    fish_rows = [[ftype, total_fish_types.get(ftype, 0)] for ftype in fish_types]
    print(tabulate(fish_rows, headers=["Fish Type", "Caught"], tablefmt="simple"))


def run_summary():
    fish_logs = load_json(FISH_FILE)
    broken_logs = load_json(BROKEN_FILE)

    if not fish_logs and not broken_logs:
        print("No logs to display.")
        return

    fish_summary, fish_types = summarize_fishing(fish_logs)
    broken_summary = summarize_broken_rods(broken_logs)
    print_summary(fish_summary, broken_summary, fish_types)


if __name__ == "__main__":
    run_summary()
