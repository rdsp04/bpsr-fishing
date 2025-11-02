import json
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate
from pathlib import Path
from statistics import mean

from src.fish.fish_service import FishService
from src.utils.path import get_data_dir
from src.utils.keybinds import (
    resolve_key,
    key_to_str,
    set_key,
    get_key,
    DEFAULT_KEYS,
    capture_and_set_key,
)


BASE = get_data_dir()
FISH_FILE = BASE / "logs/fishing_log.json"
BROKEN_FILE = BASE / "logs/broken_rods.json"
CONFIG_PATH = BASE / "config/fish_config.json"

DEFAULT_SETTINGS = {
    "resolution": "1920x1080",
    "auto_bait_purchase": "T1",
    "auto_rods_purchase": "T1",
    **DEFAULT_KEYS,
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

    def get_daily_table(self, date):
        self.refresh()
        if date not in self.fish_summary:
            return f"<p>No data for {date}</p>"

        hours = self.fish_summary[date]
        broken = self.broken_summary.get(date, {})

        total_caught = sum(h["catch"] for h in hours.values())
        total_missed = sum(h["fail"] for h in hours.values())
        total_xp = sum(h["xp"] for h in hours.values())
        total_hours = len(hours)
        avg_xp_hour = total_xp / total_hours if total_hours else 0

        total_all = total_caught + total_missed
        catch_rate = (total_caught / total_all * 100) if total_all else 0

        fish_counts = {ft: 0 for ft in self.fish_types}
        for h in hours.values():
            for ft, cnt in h["fish_types"].items():
                fish_counts[ft] += cnt

        filtered_fish = {k: v for k, v in fish_counts.items() if v > 0}
        sorted_fish = sorted(filtered_fish.items(), key=lambda x: x[1], reverse=True)

        total_fish_time = 0
        try:
            with open("logs/sessions.json", "r", encoding="utf-8") as f:
                sessions = json.load(f)

            for sess in sessions:
                start_str = sess.get("start")
                stop_str = sess.get("stop")
                if not start_str or not stop_str:
                    continue

                try:
                    start_dt = datetime.fromisoformat(start_str)
                    stop_dt = datetime.fromisoformat(stop_str)
                except Exception:
                    continue

                if start_dt.date().isoformat() == date:
                    delta = stop_dt - start_dt
                    total_fish_time += delta.total_seconds() / 60

        except Exception as e:
            print("Error loading sessions sessions:", e)

        hours_part = int(total_fish_time // 60)
        minutes_part = int(total_fish_time % 60)
        formatted_time = f"{hours_part}h {minutes_part}m" if total_fish_time else "0h 0m"

        summary_html = f"""
        <div class="daily-summary">
            <div class="daily-metric"><span class="label">Caught</span><span class="value">{total_caught}</span></div>
            <div class="daily-metric"><span class="label">Missed</span><span class="value">{total_missed}</span></div>
            <div class="daily-metric"><span class="label">XP/hour</span><span class="value">{avg_xp_hour:.0f}</span></div>
            <div class="daily-metric"><span class="label">Catch Rate</span><span class="value">{catch_rate:.2f}%</span></div>
            <div class="daily-metric"><span class="label">Total Hours</span><span class="value">{formatted_time}</span></div>
        </div>
        """

        max_fish = max(filtered_fish.values()) if filtered_fish else 1
        bars_html = ""
        for fish, count in sorted_fish:
            width = (count / max_fish * 100) if max_fish > 0 else 0
            display_name = fish.replace("_", " ").title()
            bars_html += f"""
            <div class="fish-row">
                <span class="fish-name">{display_name}</span>
                <div class="fish-bar">
                    <div class="fish-fill" style="width:{width:.1f}%;"></div>
                </div>
                <span class="fish-count">{count}</span>
            </div>
            """

        return f"""
        <div class="daily-box">
            <h3 class="daily-date">{date}</h3>
            {summary_html}
            <div class="fish-graph">{bars_html}</div>
        </div>
        """


    def get_all_daily_tables(self):
        html = ""
        for date in sorted(self.fish_summary.keys()):
            html += self.get_daily_table(date)
        return html

    def get_overall_summary(self):
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

        html = """
        <div class="summary-table">
          <table class="data-table">
            <thead>
              <tr>
                <th style="text-align:center;">TOTAL CAUGHT</th>
                <th style="text-align:center;">TOTAL MISSED</th>
                <th style="text-align:center;">TOTAL BROKEN RODS</th>
                <th style="text-align:center;">OVERALL CATCH RATE</th>
                <th style="text-align:center;">AVG FISH/MIN</th>
                <th style="text-align:center;">TOTAL XP</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:right;">{total_caught}</td>
                <td style="text-align:right;">{total_failed}</td>
                <td style="text-align:right;">{total_broken}</td>
                <td style="text-align:right;">{overall_rate:.2f}%</td>
                <td style="text-align:right;">{avg_fpm:.2f}</td>
                <td style="text-align:right;">{total_xp}</td>
              </tr>
            </tbody>
          </table>
        </div>
        """.format(
            total_caught=total_caught,
            total_failed=total_failed,
            total_broken=total_broken,
            overall_rate=overall_rate,
            avg_fpm=avg_fpm,
            total_xp=total_xp,
        )

        max_count = max(total_fish_types.values()) if total_fish_types else 1
        fish_type_bars = ""
        for ft, count in sorted(
            total_fish_types.items(), key=lambda x: x[1], reverse=True
        ):
            width_percent = (count / max_count) * 100
            fish_type_bars += f"""
                <div style='display: flex; align-items: center; margin-bottom: 6px;'>
                    <span style='width: 160px; text-transform: capitalize; color: #aeeaff; font-weight: 500;'>{ft.replace('_', ' ')}</span>
                    <div style='flex-grow: 1; background: linear-gradient(90deg, rgba(0,180,255,0.15), rgba(0,255,200,0.35)); border-radius: 6px; height: 10px; margin: 0 10px; position: relative; overflow: hidden;'>
                        <div style='width: {width_percent:.1f}%; height: 100%; background: linear-gradient(90deg, #00b4ff, #00ffc8); border-radius: 6px;'></div>
                    </div>
                    <span style='color: #fff; font-weight: bold; min-width: 40px; text-align: right;'>{count}</span>
                </div>
            """

        return f"""
            <h3 style='margin-bottom: 6px;'>Overall Stats</h3>
            <div style='overflow-x:auto; background:#111827; border-radius:8px; padding:10px;'>
                {html}
            </div>
            <h3 style='margin-top:16px;'>Fish Types</h3>
            <div style='margin-top: 10px; background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: 10px;'>
                {fish_type_bars}
            </div>
        """

    def get_fish_types_html(self):
        self.refresh()
        total_fish_types = defaultdict(int)

        for date, hours in self.fish_summary.items():
            for hour, counts in hours.items():
                for ft, c in counts["fish_types"].items():
                    total_fish_types[ft] += c

        html = '<div class="fish-type-summary">'
        for ft, count in sorted(total_fish_types.items(), key=lambda x: x[0]):
            html += f"""
                <div class="fish-entry flex justify-between">
                    <span class="fish-name">{ft}</span>
                    <span class="fish-count">{count}</span>
                </div>
            """
        html += "</div>"
        return html


class StatsApi:
    def __init__(self):
        self.stats = FishStats()
        self._settings = self._load_settings()
        self.start_key = get_key("start_key")
        self.stop_key = get_key("stop_key")
        self.fish_key = get_key("fish_key")
        self.bait_key = get_key("bait_key")
        self.rods_key = get_key("rods_key")
        self.esc_key = get_key("esc_key")

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

    def set_resolution(self, res: str):
        self._settings["resolution"] = res
        self._save_settings()

    def get_resolution(self) -> str:
        return self._settings.get("resolution", DEFAULT_SETTINGS["resolution"])

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

    def _set_key(self, name: str, key_str: str):
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
        return self.stats.get_all_daily_tables()

    def get_overall_summary(self):
        return self.stats.get_overall_summary()

    def get_fish_types_html(self):
        return self.stats.get_fish_types_html()

    def get_dates(self):
        return sorted(self.stats.fish_summary.keys())
