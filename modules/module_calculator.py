import json
import itertools

# ------------------------
# Desired stats
# ------------------------
desired_stats = ["Crit Focus", "Elite Strike", "Special Attack"]
desired_stats_norm = [s.lower() for s in desired_stats]

# ------------------------
# Load JSON
# ------------------------
with open("modules_stats.json", "r") as f:
    data = json.load(f)


# ------------------------
# Helper functions
# ------------------------
def clean_stat_name(name):
    return name.split("+")[0].strip()


def parse_value_from_name(name):
    parts = name.split("+")
    if len(parts) < 2:
        return 0
    val_str = (
        parts[1].replace("o", "0").replace("O", "0").replace("l", "1").replace("L", "1")
    )
    try:
        return int(val_str)
    except ValueError:
        return 0


# ------------------------
# Module class
# ------------------------
class Module:
    def __init__(self, index, statA, statB):
        self.name = f"Module{index}"
        self.statA = statA
        self.statB = statB

    def __repr__(self):
        return f"{self.name}: statA={self.statA}, statB={self.statB}"


# ------------------------
# Filter modules
# ------------------------
modules = []
for i, item in enumerate(data, start=1):
    statA_raw = item.get("statA", {}).get("name", "")
    statB_raw = item.get("statB", {}).get("name", "")

    statA_name_clean = clean_stat_name(statA_raw)
    statB_name_clean = clean_stat_name(statB_raw)

    if (
        statA_name_clean.lower() in desired_stats_norm
        or statB_name_clean.lower() in desired_stats_norm
    ):
        module = Module(
            i,
            {"name": statA_name_clean, "value": parse_value_from_name(statA_raw)},
            {"name": statB_name_clean, "value": parse_value_from_name(statB_raw)},
        )
        modules.append(module)

print(f"Filtered modules ({len(modules)}):")
for m in modules:
    print(m)

# ------------------------
# Define breakpoints
# ------------------------
breakpoints = [
    (20, 20),
    (20, 16),
    (16, 20),
    (20, 0),
    (0, 20),
]

# ------------------------
# Dynamic combination size
# ------------------------
COMBO_SIZE = 2  # change this to combine 2, 3, 4... modules

# ------------------------
# Generate combinations
# ------------------------
valid_combinations = []

print(f"\nChecking combinations of {len(modules)} modules (size {COMBO_SIZE})...\n")

for combo in itertools.combinations(modules, COMBO_SIZE):
    # Sum totals per desired stat
    totals = {stat: 0 for stat in desired_stats_norm}
    for mod in combo:
        for stat in [mod.statA, mod.statB]:
            name_norm = stat["name"].lower()
            if name_norm in desired_stats_norm:
                totals[name_norm] += stat["value"]

    # Check breakpoints against any permutation of totals
    for bp in breakpoints:
        stat_values = list(totals.values())
        bp_list = list(bp)

        match = any(
            all(sv >= b for sv, b in zip(stat_perm, bp_list))
            for stat_perm in itertools.permutations(stat_values, len(bp_list))
        )

        if match:
            valid_combinations.append(
                {
                    "modules": tuple(mod.name for mod in combo),
                    "totals": totals.copy(),
                    "breakpoint": bp,
                    "module_stats": [
                        {"statA": mod.statA, "statB": mod.statB} for mod in combo
                    ],
                }
            )
            print(
                f"✅ Combo {', '.join(mod.name for mod in combo)} matches breakpoint {bp} -> totals: {totals}"
            )
            break

# ------------------------
# Print results with stats
# ------------------------
print("\n=== Valid combinations ===")
for combo in valid_combinations:
    print(f"Modules: {combo['modules']}")
    for i, mod_stats in enumerate(combo["module_stats"], start=1):
        print(
            f"  {combo['modules'][i-1]} -> statA: {mod_stats['statA']}, statB: {mod_stats['statB']}"
        )
    totals = combo["totals"]
    print(
        f"Totals -> Crit Focus: {totals.get('crit focus', 0)}, "
        f"Elite Strike: {totals.get('elite strike', 0)}, "
        f"Special Attack: {totals.get('special attack', 0)}, "
        f"Breakpoint met: {combo['breakpoint']}\n"
    )
