"""Profiles for the pizza and deviation radar, and team style for the pre-match radar. Always inside one league."""
from __future__ import annotations

import numpy as np
import pandas as pd

PM = [("Shooting", "xg_p90", "xG"), ("Shooting", "opta_npxg_p90", "npxG (Opta)"), ("Creating", "opta_xa_p90", "xA (Opta)"),
      ("Creating", "xd_added_p90", "xDanger added"), ("Creating", "xd_received_p90", "xDanger received"),
      ("Possession", "net_p90", "Net value (M3)"), ("Possession", "pae_100", "xPass +/100 (M4)"),
      ("Possession", "sb_obv_90", "OBV (StatsBomb)"), ("Possession", "opta_wtv_p90", "WTV (Opta)"),
      ("Defending", "xd_won_p90", "xDanger won"), ("Defending", "xd_denied_p90", "xDanger denied"),
      ("Defending", "imp_won_aerial_duels_p90", "Aerials won"), ("Physical", "sc_psv99", "Top speed"),
      ("Physical", "sc_hi_distance_full_all_p90", "HI distance"), ("Physical", "sc_sprint_count_full_all_p90", "Sprints"),
      ("Overall", "wa_rating", "WA rating (M5)"), ("Overall", "wa_composite", "WA composite")]
MIN_POOL = 450


def pos_pool(scouting: pd.DataFrame, pos):
    return scouting[(scouting.pos_group == pos) & (scouting.minutes.fillna(0) >= MIN_POOL)]


def profile_rows(scouting: pd.DataFrame, player: pd.Series) -> list[dict]:
    pool = pos_pool(scouting, player.pos_group)
    out = []
    for cat, k, lab in PM:
        v = player.get(k)
        vals = pool[k].dropna() if k in pool else pd.Series(dtype=float)
        if v is None or pd.isna(v) or len(vals) < 5:
            out.append(dict(category=cat, metric=lab, key=k, value=None if v is None or pd.isna(v) else float(v),
                            percentile=None, z=None, position_avg=None, pool=len(vals)))
            continue
        mu, sd = vals.mean(), vals.std() or 1.0
        out.append(dict(category=cat, metric=lab, key=k, value=float(v), percentile=int(round((vals <= v).mean() * 100)),
                        z=round(float((v - mu) / sd), 2), position_avg=round(float(mu), 3), pool=len(vals)))
    return out


def team_style(p: dict) -> tuple[list[str], pd.DataFrame, pd.DataFrame]:
    """(metrics, raw per team, z per team). 'Prevented' metrics carry a minus sign so higher is always better."""
    acc = {}
    for m in p["matches"]:
        if m.get("status") != "played" or not m.get("post"):
            continue
        for t, i in ((m["home"], 0), (m["away"], 1)):
            s = m["post"]["stats"][i]
            a = acc.setdefault(t, dict(n=0, poss=0, field_tilt=0, box_entries=0, high_regains=0, corners=0))
            a["n"] += 1
            for k in ("poss", "field_tilt", "box_entries", "high_regains", "corners"):
                a[k] += s.get(k) or 0
    rows = {}
    for t in p["table"]:
        a = acc.get(t["team"], dict(n=1))
        n = max(a["n"], 1)
        T = p["setpieces"]["teams"].get(t["team"], {})
        gk = (T.get("options_for") or {}).get("Goal kick") or []
        tot = sum(o[1] for o in gk) or 1
        ogk = ((T.get("against") or {}).get("Goal kick") or {}).get("ret")
        rows[t["team"]] = {
            "xG for": t["xg_f"], "xDanger for": t["xd_f"], "Set-piece xG for": t["sp_xg_f"],
            "xG prevented": -t["xg_a"], "xDanger prevented": -t["xd_a"], "Set-piece xG prevented": -t["sp_xg_a"],
            "Possession": a.get("poss", 0) / n, "Field tilt": a.get("field_tilt", 0) / n,
            "Box entries": a.get("box_entries", 0) / n, "High regains": a.get("high_regains", 0) / n,
            "Corners won": a.get("corners", 0) / n,
            "Short goal kicks": sum(o[1] for o in gk if o[0].startswith("Short")) / tot,
            "Press on opp. goal kicks": None if ogk is None else -ogk}
    raw = pd.DataFrame(rows).T.astype(float)
    z = (raw - raw.mean()) / raw.std(ddof=1).replace(0, 1)
    return list(raw.columns), raw, z


def scouting_frame(p: dict) -> pd.DataFrame:
    df = pd.DataFrame(p["scouting"])
    for c in df.columns:
        if c not in ("name", "team", "pos_group", "foot", "contract_until", "tm_profile_url", "sp_del", "sp_fin"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def rows_of(arr, keys):
    return [dict(zip(keys, a)) for a in (arr or [])]
