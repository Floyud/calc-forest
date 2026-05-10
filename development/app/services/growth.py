from __future__ import annotations

import json
from pathlib import Path

from app.schemas import EncouragementRule, TreeSpecies


_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(filename: str) -> list[dict]:
    file_path = _DATA_DIR / filename
    return json.loads(file_path.read_text(encoding="utf-8"))


def list_tree_species() -> list[TreeSpecies]:
    return [TreeSpecies(**_map_species(item)) for item in _load_json("tree_species.json")]


def _map_species(item: dict) -> dict:
    item = {**item}
    if "id" in item and "species_id" not in item:
        item["species_id"] = item.pop("id")
    return item


def list_encouragement_rules() -> list[EncouragementRule]:
    return [EncouragementRule(**item) for item in _load_json("encouragements.json")]


def get_tree_species_by_id(tree_species_id: str | None) -> TreeSpecies | None:
    if not tree_species_id:
        return None

    for item in list_tree_species():
        if item.species_id == tree_species_id:
            return item
    return None


def get_encouragement_message(
    *,
    trigger: str,
    cumulative_days: int | None = None,
    start_grade: int | None = None,
) -> str | None:
    rules = list_encouragement_rules()

    candidates = []
    for rule in rules:
        if rule.trigger != trigger:
            continue
        if start_grade is not None and rule.start_grade not in {None, start_grade}:
            continue
        if cumulative_days is not None and rule.cumulative_days is not None:
            if cumulative_days < rule.cumulative_days:
                continue
        candidates.append(rule)

    if not candidates:
        for rule in rules:
            if rule.trigger == trigger and rule.cumulative_days is None and rule.start_grade is None:
                return rule.message
        return None

    best = max(candidates, key=lambda r: r.cumulative_days or 0)
    return best.message
