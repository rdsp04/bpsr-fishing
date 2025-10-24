import webview
import json
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate
from src.fish.fish_service import FishService  # adjust path if needed

FISH_FILE = "logs/fishing_log.json"
BROKEN_FILE = "logs/broken_rods.json"
CONFIG_PATH = "src/fish/fish_config.json"


class UiApi:
    def __init__(self):
        self.is_top = False

    def toggle_top(self):
        window = webview.windows[0]
        self.is_top = not self.is_top
        window.toggle_always_on_top()
        return "Pinned to top" if self.is_top else "Unpinned"

    # New method
    def get_summary_table(self):
        fish_logs = self.load_json(FISH_FILE)
        broken_logs = self.load_json(BROKEN_FILE)
        fish_xp = self.get_fish_xp_map()

        if not fish_logs and not broken_logs:
            return "<p>No logs to display.</p>"

        fish_summary, fish_types = self.summarize_fishing(fish_logs, fish_xp)
        broken_summary = self.summarize_broken_rods(broken_logs)

        # Generate HTML table for first date only (simplified)
        date, hours = next(iter(fish_summary.items()))
        rows = []
        for hour, counts in sorted(hours.items()):
            broken = broken_summary[date].get(hour, 0)
            total = counts["catch"] + counts["fail"]
            rate = (counts["catch"] / total * 100) if total else 0
            xp_hour = counts["xp"]
            type_counts = [counts["fish_types"].get(ft, 0) for ft in fish_types]

            rows.append(
                [
                    hour,
                    counts["catch"],
                    counts["fail"],
                    broken,
                    f"{rate:.2f}%",
                    xp_hour,
                    *type_counts,
                ]
            )
        headers = [
            "Hour",
            "Caught",
            "Missed",
            "Broken Rods",
            "Catch Rate",
            "XP/Hour",
        ] + fish_types
        html_table = tabulate(rows, headers=headers, tablefmt="html")
        return html_table

    # Utility functions
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


def start_ui():
    api = UiApi()
    html = """
    <!DOCTYPE html>
    <html>
    <body style="background-color:#222; color:white; font-family:sans-serif; text-align:center; padding:20px;">
        <h1>Fisher Control Panel</h1>
        <button id="toggle" style="padding:10px 20px; margin:5px; background:#444; color:white; border:none; border-radius:5px; cursor:pointer;">Pin to Top</button>
        <button id="summary" style="padding:10px 20px; margin:5px; background:#444; color:white; border:none; border-radius:5px; cursor:pointer;">Show Summary</button>
        <div id="status" style="margin-top:20px; overflow:auto; max-height:400px;"></div>

        <script>
        document.getElementById('toggle').onclick = () => {
            window.pywebview.api.toggle_top().then(result => {
                alert(result);
            });
        };

        document.getElementById('summary').onclick = () => {
            window.pywebview.api.get_summary_table().then(html => {
                document.getElementById('status').innerHTML = html;
            });
        };
        </script>
    </body>
    </html>
    """

    # Window 2
    html2 = """
    <html>
    <body style="background:rgba(0,0,0,0); color:white; font-family:sans-serif; text-align:center; padding:50px;">
        <h1>Overlay Window 2</h1>
        <p>This is a second overlay window</p>
    </body>
    </html>
    """


    webview.create_window(
        "Overlay 2",
        html=html2,
        width=300,
        height=150,
        resizable=True,
        frameless=True,
        transparent=True,
        on_top=True
    )

    webview.create_window(
        "bpsr-fishing",
        html=html,
        js_api=api,
        width=800,
        height=600,
        min_size=(400,300),
        resizable=True,
        frameless=False,
        transparent=True,
        minimized=True,
        on_top=True,
    )
    webview.start(debug=False, http_server=False)


if __name__ == "__main__":
    start_ui()
