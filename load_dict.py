"""Utilities for loading the CC-CEDICT dataset with caching support."""

from __future__ import annotations

import json
import os
import tempfile
from os.path import abspath, dirname, join
from typing import Dict, List, Optional


__all__ = ["load_dict"]

CEDICT_FILENAME = "cedict_ts.u8"
CACHE_FILENAME = "cedict_cache.json"
_BASE_DIR = dirname(abspath(__file__))


def _source_path() -> str:
    return join(_BASE_DIR, CEDICT_FILENAME)


def _cache_path() -> str:
    return join(_BASE_DIR, CACHE_FILENAME)


def _source_metadata(path: str) -> Dict[str, int]:
    stat = os.stat(path)
    return {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}


def _load_cache(cache_path: str, expected_meta: Dict[str, int]) -> Optional[Dict[str, Dict[str, object]]]:
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as cache_file:
            payload = json.load(cache_file)
    except (json.JSONDecodeError, OSError):
        return None

    metadata = payload.get("metadata")
    data = payload.get("data")

    if not isinstance(metadata, dict) or not isinstance(data, dict):
        return None

    if metadata.get("mtime_ns") != expected_meta["mtime_ns"] or metadata.get("size") != expected_meta["size"]:
        return None

    return data


def _write_cache(cache_path: str, data: Dict[str, Dict[str, object]], metadata: Dict[str, int]) -> None:
    payload = {"metadata": metadata, "data": data}
    os.makedirs(dirname(cache_path), exist_ok=True)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=_BASE_DIR, delete=False) as temp_file:
        json.dump(payload, temp_file)
        temp_name = temp_file.name

    os.replace(temp_name, cache_path)


def _parse_line(line: str) -> Optional[Dict[str, object]]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.rstrip("/").split("/")
    if len(parts) <= 1:
        return None

    char_and_pinyin = parts[0].split("[")
    if len(char_and_pinyin) != 2:
        return None

    characters = char_and_pinyin[0].strip().split()
    if len(characters) < 2:
        return None

    pinyin = char_and_pinyin[1].rstrip().rstrip("]")
    english_entries = [entry for entry in parts[1:] if entry]

    return {
        "traditional": characters[0],
        "simplified": characters[1],
        "pinyin": pinyin,
        "english": english_entries,
    }


def _remove_surnames(entries: List[Dict[str, object]]) -> None:
    for idx in range(len(entries) - 1, -1, -1):
        english_entries = entries[idx].get("english", [])
        if not isinstance(english_entries, list):
            continue

        if any(str(item).startswith("surname ") for item in english_entries):
            next_idx = idx + 1
            if next_idx < len(entries) and entries[idx]["traditional"] == entries[next_idx]["traditional"]:
                entries.pop(idx)


def _build_dictionary(raw_path: str) -> Dict[str, Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    with open(raw_path, encoding="utf-8") as cedict_file:
        for raw_line in cedict_file:
            parsed = _parse_line(raw_line)
            if parsed:
                entries.append(parsed)

    _remove_surnames(entries)

    dictionary: Dict[str, Dict[str, object]] = {}
    for entry in entries:
        dictionary[entry["simplified"]] = entry

    return dictionary


def load_dict() -> Dict[str, Dict[str, object]]:
    """Load the CC-CEDICT dictionary, caching the parsed output on disk."""

    source_path = _source_path()
    metadata = _source_metadata(source_path)
    cache_path = _cache_path()

    cached = _load_cache(cache_path, metadata)
    if cached is not None:
        return cached

    dictionary = _build_dictionary(source_path)
    _write_cache(cache_path, dictionary, metadata)
    return dictionary
