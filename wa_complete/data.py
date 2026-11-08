"""Read the league files written by the WA Match Hub daily agent, locally or from its private Neon database.

Where the data comes from, first hit wins:
  1. WA_HUB_DATA environment variable (a folder with <KEY>/WA_Hub_*.json)
  2. ./data in this repo (same layout; git-ignored)
  3. the agent's own exports: ~/Downloads/Agents/WA Match Hub 26-27/web/exports  (on the Mac that runs the agent)
  4. Neon (online; WA_HUB_SOURCE=neon forces it): the agent uploads every league after its daily run; the app reads with the read-only URL in
     st.secrets["neon"]["url"] (or the WA_HUB_DB environment variable)
"""
from __future__ import annotations

import gzip
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


# ----------------------------------------------------------------------------- local files
def root() -> Path | None:
    if os.getenv("WA_HUB_SOURCE") == "neon":       # force the online copy (testing)
        return None
    for c in CANDIDATES:
        if c.exists() and any(c.glob("*/WA_Hub_*.json")):
            return c
    return None


def _local_files(key: str) -> dict:
    r = root()
    if r is None:
        return {}
    out = {}
    for f in (r / key).glob("WA_Hub_*"):
        if f.name.endswith("_csv.zip"):
            out["csv"] = f
        elif f.suffix == ".json":
            out["json"] = f
        elif f.suffix == ".xlsx":
            out["xlsx"] = f
    return out


# ----------------------------------------------------------------------------- Neon
def neon_url() -> str | None:
    if os.getenv("WA_HUB_DB"):
        return os.environ["WA_HUB_DB"]
    try:
        return st.secrets["neon"]["url"]
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _neon_index(url: str) -> dict:
    """{league: {kind: (filename, updated iso)}} (refreshed every 5 minutes)."""
    import psycopg
    with psycopg.connect(url, connect_timeout=20) as c:
        rows = c.execute("SELECT league, kind, filename, updated FROM hub_files").fetchall()
    out = {}
    for lg, kind, fn, upd in rows:
        out.setdefault(lg, {})[kind] = (fn, upd.isoformat())
    return out


@st.cache_data(show_spinner="Loading league…", max_entries=12)
def _neon_blob(url: str, key: str, kind: str, updated: str) -> bytes:   # updated in the key: new upload, new fetch
    import psycopg
    with psycopg.connect(url, connect_timeout=20) as c:
        row = c.execute("SELECT content FROM hub_files WHERE league = %s AND kind = %s", (key, kind)).fetchone()
    return bytes(row[0]) if row else b""


def source() -> str:
    if root() is not None:
        return f"local files: {root()}"
    return "Neon (online copy, uploaded by the daily agent)" if neon_url() else "none"


def _neon_ok() -> dict:
    url = neon_url()
    if not url:
        return {}
    try:
        return _neon_index(url)
    except Exception as ex:
        st.sidebar.error(f"Could not reach the online data: {type(ex).__name__}")
        return {}


# ----------------------------------------------------------------------------- public API
def available() -> list[tuple[str, str, str]]:
    if root() is not None:
        return [lg for lg in LEAGUES if _local_files(lg[0]).get("json")]
    idx = _neon_ok()
    return [lg for lg in LEAGUES if "json" in idx.get(lg[0], {})]


def league_file(key: str, kind: str) -> tuple[str, bytes] | None:
    """(filename, bytes) of the league's xlsx / csv zip / json, wherever it lives."""
    f = _local_files(key).get(kind)
    if f:
        return f.name, f.read_bytes()
    idx = _neon_ok().get(key, {})
    if kind in idx:
        fn, upd = idx[kind]
        b = _neon_blob(neon_url(), key, kind, upd)
        if kind == "json":
            return fn.removesuffix(".gz"), gzip.decompress(b)
        return fn, b
    return None


@st.cache_data(show_spinner="Loading league…", max_entries=4)
def _load_local(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(key: str) -> dict | None:
    f = _local_files(key).get("json")
    if f:
        return _load_local(str(f), f.stat().st_mtime)   # mtime in the key: a new daily run reloads automatically
    idx = _neon_ok().get(key, {})
    if "json" not in idx:
        return None
    return _parse(_neon_blob(neon_url(), key, "json", idx["json"][1]), idx["json"][1])


@st.cache_data(show_spinner=False, max_entries=4)
def _parse(blob: bytes, updated: str) -> dict:
    return json.loads(gzip.decompress(blob))
