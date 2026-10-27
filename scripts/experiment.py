"""Shared scenario selection for Isaac, ROS nodes, and offline tools."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_experiment(scenario=None):
    config = json.loads((ROOT / "config/experiment.json").read_text())
    catalog = json.loads((ROOT / "config/scenarios.json").read_text())
    active = ROOT / "config/active_scenario.json"
    selected = scenario or os.environ.get("ROV_SCENARIO") or (
        json.loads(active.read_text())["scenario"] if active.exists() else "slalom")
    if selected not in catalog:
        raise ValueError(f"Unknown scenario {selected!r}; choose {', '.join(catalog)}")
    config.update(catalog[selected])
    config["scenario"] = selected
    config["scene_file"] = str(ROOT / "scenes" / f"pool_{selected}.usda")
    override_file = os.environ.get("ROV_EXPERIMENT_OVERRIDES")
    if override_file:
        overrides = json.loads(Path(override_file).read_text())
        if set(overrides)-set(config):
            raise ValueError(f"Unknown experiment overrides: {set(overrides)-set(config)}")
        config.update(overrides)
        config["overrides_file"] = str(Path(override_file).resolve())
    return config
