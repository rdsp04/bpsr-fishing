import json
from pathlib import Path
from src.utils.path import get_data_dir


def fix_spelling():
    filename = get_data_dir() / "logs" / "fishing_log.json"
    if not filename.exists():
        print(f"No log file found at {filename}")
        return

    with open(filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Invalid JSON file, cannot fix.")
            return

    def correct_text(text):
        corrections = {
            "astercad": "asterscad",
            "aluminium": "aluminum"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right).replace(wrong.capitalize(), right.capitalize())
        return text

    def fix_item(item):
        if isinstance(item, dict):
            return {k: fix_item(correct_text(v) if isinstance(v, str) else v) for k, v in item.items()}
        elif isinstance(item, list):
            return [fix_item(i) for i in item]
        return item

    fixed_data = fix_item(data)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=2)

    print(f"Fixed naming issues in: {filename}")
