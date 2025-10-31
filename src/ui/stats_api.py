import json
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate
from pathlib import Path
from src.fish.fish_service import FishService
from src.utils.path import get_data_dir
from src.utils.keybinds import resolve_key, key_to_str, set_key, get_key, DEFAULT_KEYS, capture_and_set_key


BASE = get_data_dir()
FISH_FILE = BASE / "logs/fishing_log.json"
BROKEN_FILE = BASE / "logs/broken_rods.json"
CONFIG_PATH = BASE / "config/fish_config.json"

DEFAULT_SETTINGS = {
    "resolution": "1920x1080",
    "auto_bait_purchase": "T1",
    "auto_rods_purchase": "T1",
    **DEFAULT_KEYS
}
SETTINGS_FILE = BASE / "config/settings.json"


class FishStats:
    def __init__(self):
        self.fish_logs = self.load_json(FISH_FILE)
        self.broken_logs = self.load_json(BROKEN_FILE)
        self.fish_xp = self.get_fish_xp_map()
        self.fish_summary, self.fish_types = self.summarize_fishing(
            self.fish_logs, self.fish_xp
        )
        self.broken_summary = self.summarize_broken_rods(self.broken_logs)

    def refresh(self):
        self.fish_logs = self.load_json(FISH_FILE)
        self.broken_logs = self.load_json(BROKEN_FILE)
        self.fish_summary, self.fish_types = self.summarize_fishing(
            self.fish_logs, self.fish_xp
        )
        self.broken_summary = self.summarize_broken_rods(self.broken_logs)

    def load_json(self, filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_fish_xp_map(self):
        service = FishService(CONFIG_PATH)
        service.load_fishes()
        return {fish.id: fish.xp for fish in service.get_all()}

    def summarize_fishing(self, logs, fish_xp):
        summary = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "catch": 0,
                    "fail": 0,
                    "xp": 0,
                    "times": [],
                    "fish_types": defaultdict(int),
                }
            )
        )
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

    def summarize_broken_rods(self, logs):
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

    def calculate_fish_per_minute(self, times):
        if len(times) < 2:
            return 0
        return len(times) / 60

    # -----------------------
    # HTML / API helpers
    # -----------------------
    def get_daily_table(self, date):
        self.refresh()
        """Return HTML table for a specific day"""
        if date not in self.fish_summary:
            return f"<p>No data for {date}</p>"

        rows = []
        hours = self.fish_summary[date]
        broken = self.broken_summary.get(date, {})

        for hour, counts in sorted(hours.items()):
            total = counts["catch"] + counts["fail"]
            rate = (counts["catch"] / total * 100) if total else 0
            fpm = self.calculate_fish_per_minute(counts["times"])
            type_counts = [counts["fish_types"].get(ft, 0) for ft in self.fish_types]
            rows.append(
                [
                    hour,
                    counts["catch"],
                    counts["fail"],
                    broken.get(hour, 0),
                    f"{rate:.2f}%",
                    f"{fpm:.2f}",
                    counts["xp"],
                    *type_counts,
                ]
            )

        headers = [
            "Hour",
            "Caught",
            "Missed",
            "Broken Rods",
            "Catch Rate",
            "Fish/Min",
            "XP/Hour",
        ] + self.fish_types
        return tabulate(rows, headers=headers, tablefmt="html")

    def get_all_daily_tables(self):
        """Return HTML with one table per day for all recorded dates"""
        html = ""
        for date in sorted(self.fish_summary.keys()):
            daily_table = self.get_daily_table(date)  # reuse existing method
            html += f'<div class="mb-6">'
            html += f'<h2 class="text-lg font-semibold mb-2">{date}</h2>'
            html += f'<div class="overflow-x-auto bg-gray-800 rounded p-2">{daily_table}</div>'
            html += "</div>"
        return html

    def get_overall_summary(self):
        """Return HTML table for totals and averages"""
        total_caught = total_failed = total_broken = total_xp = 0
        total_fish_types = defaultdict(int)

        for date, hours in self.fish_summary.items():
            broken = self.broken_summary.get(date, {})
            for hour, counts in hours.items():
                total_caught += counts["catch"]
                total_failed += counts["fail"]
                total_broken += broken.get(hour, 0)
                total_xp += counts["xp"]
                for ft, c in counts["fish_types"].items():
                    total_fish_types[ft] += c

        total_fish = total_caught + total_failed
        overall_rate = (total_caught / total_fish * 100) if total_fish else 0
        avg_fpm = (total_caught / 60) if total_fish else 0

        main_table = tabulate(
            [
                [
                    total_caught,
                    total_failed,
                    total_broken,
                    f"{overall_rate:.2f}%",
                    f"{avg_fpm:.2f}",
                    total_xp,
                ]
            ],
            headers=[
                "Total Caught",
                "Total Missed",
                "Total Broken Rods",
                "Overall Catch Rate",
                "Avg Fish/Min",
                "Total XP",
            ],
            tablefmt="html",
        )

        fish_type_table = tabulate(
            [[ft, total_fish_types.get(ft, 0)] for ft in self.fish_types],
            headers=["Fish Type", "Caught"],
            tablefmt="html",
        )

        return f"<h3>Overall Stats</h3>{main_table}<h3>Fish Types</h3>{fish_type_table}"


class StatsApi:
    def __init__(self):
        self.stats = FishStats()
        self._settings = self._load_settings()

        # preload keys
        self.start_key = get_key("start_key")
        self.stop_key = get_key("stop_key")
        self.fish_key = get_key("fish_key")
        self.bait_key = get_key("bait_key")
        self.rods_key = get_key("rods_key")
        self.esc_key = get_key("esc_key")

    # --- Settings file load/save ---
    def _load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return DEFAULT_SETTINGS.copy()

    def _save_settings(self):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._settings, f, indent=2)

    # --- Resolution ---
    def set_resolution(self, res: str):
        self._settings["resolution"] = res
        self._save_settings()

    def get_resolution(self) -> str:
        return self._settings.get("resolution", DEFAULT_SETTINGS["resolution"])

    # --- Auto bait / rod ---
    def set_auto_bait(self, bait: str):
        self._settings["auto_bait_purchase"] = bait
        self._save_settings()

    def get_auto_bait(self) -> str:
        return self._settings.get(
            "auto_bait_purchase", DEFAULT_SETTINGS["auto_bait_purchase"]
        )

    def set_auto_rod(self, rod: str):
        self._settings["auto_rods_purchase"] = rod
        self._save_settings()

    def get_auto_rod(self) -> str:
        return self._settings.get(
            "auto_rods_purchase", DEFAULT_SETTINGS["auto_rods_purchase"]
        )

    # --- Keybinds ---
    def set_key(self, name: str, key_str: str):
        if name not in DEFAULT_KEYS:
            raise ValueError(f"Invalid key name: {name}")
        resolved = resolve_key(key_str)
        if not resolved:
            raise ValueError(f"Invalid key: {key_str}")
        self.keys[name] = resolved
        self._settings[name] = key_str
        set_key(name, key_str)
        self._save_settings()
        return key_str

    def get_key(self, name: str):
        if name not in DEFAULT_KEYS:
            raise ValueError(f"Invalid key name: {name}")
        return get_key(name)


    def capture_key_for(self, name: str):
        if name not in DEFAULT_KEYS:
            raise ValueError(f"Invalid key name: {name}")
        key_str = capture_and_set_key(name)
        return key_str
    # --- Stats functions ---
    def get_daily_table(self):
        self.stats.refresh()
        return self.stats.get_all_daily_tables()

    def get_overall_summary(self):
        self.stats.refresh()
        return self.stats.get_overall_summary()

    def get_dates(self):
        self.stats.refresh()
        return sorted(self.stats.fish_summary.keys())
