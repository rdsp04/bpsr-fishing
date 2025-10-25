import json
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate
from src.fish.fish_service import FishService  # adjust path if needed

from src.utils.path import get_data_dir

BASE = get_data_dir()
FISH_FILE = BASE / "logs/fishing_log.json"
BROKEN_FILE = BASE / "logs/broken_rods.json"
CONFIG_PATH = BASE / "config/fish_config.json"
SESSIONS_FILE = BASE / "logs/sessions.json"


def load_sessions():
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_sessions(sessions):
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2, default=str)


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


def get_fish_xp_map():
    """Use FishService to get XP values for each fish by ID"""
    service = FishService(CONFIG_PATH)
    service.load_fishes()
    return {fish.id: fish.xp for fish in service.get_all()}


def summarize_fishing(logs, fish_xp):
    summary = defaultdict(lambda: defaultdict(lambda: {
        "catch": 0,
        "fail": 0,
        "xp": 0,
        "times": [],
        "fish_types": defaultdict(int)
    }))
    all_fish_types = set()

    for entry in logs:
        ts = entry.get("timestamp")
        status = entry.get("catch")
        fish_type = entry.get("fish_type")

        if ts is None or status is None:
            continue

        dt = datetime.fromisoformat(ts)
        date_str = dt.date().isoformat()
        hour_str = f"{dt.hour:02d}:00"

        summary[date_str][hour_str]["times"].append(dt)

        if status:
            summary[date_str][hour_str]["catch"] += 1

            # Fallback if fish_type missing or unknown
            if not fish_type or fish_type not in fish_xp:
                fish_type = "undefined"
                xp_value = 1
            else:
                xp_value = fish_xp[fish_type]

            summary[date_str][hour_str]["fish_types"][fish_type] += 1
            summary[date_str][hour_str]["xp"] += xp_value
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
    return len(times) / 60  # fish per hour block


def print_summary(fish_summary, broken_summary, fish_types):
    total_caught = 0
    total_failed = 0
    total_broken = 0
    total_xp = 0
    total_fish_types = defaultdict(int)

    for date, hours in sorted(fish_summary.items()):
        print(f"\nDate: {date}")
        rows = []
        day_caught = 0
        day_failed = 0
        day_xp = 0

        for hour, counts in sorted(hours.items()):
            broken = broken_summary[date][hour] if date in broken_summary else 0
            total_broken += broken

            total = counts["catch"] + counts["fail"]
            rate = (counts["catch"] / total * 100) if total else 0
            fpm = calculate_fish_per_minute(counts["times"])
            xp_hour = counts["xp"]

            total_caught += counts["catch"]
            total_failed += counts["fail"]
            total_xp += xp_hour

            day_caught += counts["catch"]
            day_failed += counts["fail"]
            day_xp += xp_hour

            for ftype, count in counts["fish_types"].items():
                total_fish_types[ftype] += count

            type_counts = [counts["fish_types"].get(ft, 0) for ft in fish_types]

            rows.append([
                hour,
                counts["catch"],
                counts["fail"],
                broken,
                f"{rate:.2f}%",
                f"{fpm:.2f}",
                xp_hour,
                *type_counts
            ])

        headers = ["Hour", "Caught", "Missed", "Broken Rods", "Catch Rate", "Fish/Min", "XP/Hour"] + fish_types
        print(tabulate(rows, headers=headers, tablefmt="simple"))

        # Add daily totals
        total_fish = day_caught + day_failed
        avg_rate = (day_caught / total_fish * 100) if total_fish else 0

        print(f"\n  Total Fish: {day_caught}")
        print(f"  Total XP: {day_xp}")
        print(f"  Avg Catch Rate: {avg_rate:.2f}%")

    total_fish = total_caught + total_failed
    total_rate = (total_caught / total_fish * 100) if total_fish else 0

    print("\nTOTAL STATISTICS")
    print(tabulate(
        [[
            total_caught,
            total_failed,
            total_broken,
            f"{total_rate:.2f}%",
            f"{total_caught / 60:.2f}",
            total_xp
        ]],
        headers=["Total Caught", "Total Missed", "Total Broken Rods", "Overall Catch Rate", "Avg Fish/Min", "Total XP"],
        tablefmt="simple",
    ))

    print("\nTOTAL FISH TYPES")
    fish_rows = [[ftype, total_fish_types.get(ftype, 0)] for ftype in fish_types]
    print(tabulate(fish_rows, headers=["Fish Type", "Caught"], tablefmt="simple"))


def run_summary():
    fish_logs = load_json(FISH_FILE)
    broken_logs = load_json(BROKEN_FILE)
    fish_xp = get_fish_xp_map()

    if not fish_logs and not broken_logs:
        print("No logs to display.")
        return

    fish_summary, fish_types = summarize_fishing(fish_logs, fish_xp)
    broken_summary = summarize_broken_rods(broken_logs)
    print_summary(fish_summary, broken_summary, fish_types)


if __name__ == "__main__":
    run_summary()
