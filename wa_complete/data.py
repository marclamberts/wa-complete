"""Read the league payloads written by the WA Match Hub daily agent.

Where the data comes from, first hit wins:
  1. WA_HUB_DATA environment variable (a folder with <KEY>/WA_Hub_*.json)
  2. ./data in this repo (same layout; git-ignored, for a copy or a deployment)
  3. the agent's own exports: ~/Downloads/Agents/WA Match Hub 26-27/web/exports
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parents[1]
CANDIDATES = [Path(os.environ["WA_HUB_DATA"]).expanduser()] if os.getenv("WA_HUB_DATA") else []
CANDIDATES += [REPO / "data", Path.home() / "Downloads/Agents/WA Match Hub 26-27/web/exports"]

LEAGUES = [  # key, name, group
    ("NED1", "Eredivisie", "Netherlands"), ("BEL1", "Jupiler Pro League", "Belgium"),
    ("GER1", "Bundesliga", "Germany"), ("GER2", "2. Bundesliga", "Germany"), ("GER3", "3. Liga", "Germany"),
    ("GER4W", "Regionalliga West", "Regionalliga"), ("GER4SW", "Regionalliga Südwest", "Regionalliga"),
    ("GER4BY", "Regionalliga Bayern", "Regionalliga"), ("GER4N", "Regionalliga Nord", "Regionalliga"),
    ("GER4NO", "Regionalliga Nordost", "Regionalliga"),
]


def root() -> Path | None:
    for c in CANDIDATES:
        if c.exists() and any(c.glob("*/WA_Hub_*.json")):
            return c
    return None


def files(key: str) -> dict:
    """{'json': Path, 'xlsx': Path, 'csv': Path} for a league (whatever exists)."""
    r = root()
    if r is None:
        return {}
    d = r / key
    out = {}
    for f in d.glob("WA_Hub_*"):
        if f.name.endswith("_csv.zip"):
            out["csv"] = f
        elif f.suffix == ".json":
            out["json"] = f
        elif f.suffix == ".xlsx":
            out["xlsx"] = f
    return out


def available() -> list[tuple[str, str, str]]:
    return [lg for lg in LEAGUES if files(lg[0]).get("json")]


@st.cache_data(show_spinner="Loading league…", max_entries=4)
def _load(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(key: str) -> dict | None:
    f = files(key).get("json")
    if not f:
        return None
    return _load(str(f), f.stat().st_mtime)     # mtime in the key: a new daily run reloads automatically
