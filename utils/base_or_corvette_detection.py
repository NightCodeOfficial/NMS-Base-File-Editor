# utils/base_or_corvette_detection.py

from typing import Any, Generator
import csv

def find_key_recursively(data: Any, target_key: str, path=None) -> Generator[tuple[list[str], Any], None, None]:
    """
    Recursively search for all occurrences of a given key in a nested dict/list structure.

    Yields:
        (path, value): path as list of keys leading to the target, and the associated value
    """
    if path is None:
        path = []

    if isinstance(data, dict):
        for k, v in data.items():
            if k == target_key:
                yield path + [k], v
            yield from find_key_recursively(v, target_key, path + [k])
    elif isinstance(data, list):
        for i, item in enumerate(data):
            yield from find_key_recursively(item, target_key, path + [f"[{i}]"])


def export_bases_to_csv(bases, csv_path="output/bases_overview.csv"):
    rows = []
    for i, base in enumerate(bases):
        rows.append({
            "Index": i,
            "Name": base.get("Name", ""),
            "PersistentBaseTypes": base.get("BaseType", {}).get("PersistentBaseTypes", ""),
            "Owner_UID": base.get("Owner", {}).get("UID", ""),
            "Owner_USN": base.get("Owner", {}).get("USN", ""),
            "GameMode": base.get("GameMode", {}).get("PresetGameMode", ""),
            "Difficulty": base.get("Difficulty", {}).get("DifficultyPreset", {}).get("DifficultyPresetType", ""),
            "NumObjects": len(base.get("Objects", [])),
        })
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} bases to {csv_path}")


def get_number_of_bases_by_type(bases, base_type):
    return len([base for base in bases if base.get("BaseType", {}).get("PersistentBaseTypes", "") == base_type])

def filter_base_by_type(bases, base_type):
    return [base for base in bases if base.get("BaseType", {}).get("PersistentBaseTypes", "") == base_type]