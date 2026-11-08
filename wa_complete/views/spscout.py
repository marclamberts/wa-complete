import pandas as pd
import streamlit as st

from .. import exports
from .common import esc, heading

ZONES = ["Near post", "Six-yard centre", "Penalty spot", "Far post", "Edge of box"]


def flat(rows):
    out = []
    for r in rows:
        x = {k: v for k, v in r.items() if k not in ("zones", "pid", "threat")}
        for z in ZONES:
            x[z] = (r.get("zones") or {}).get(z)
        out.append(x)
    return pd.DataFrame(out)


def cards(defs, counts, cols=4):
    items = list(defs.items())
    for i in range(0, len(items), cols):
        cs = st.columns(cols)
        for c, (k, v) in zip(cs, items[i:i + cols]):
            c.markdown(f"<div class='wa-arch'><span class='n'>{counts.get(k, 0)}</span><b>{esc(k)}</b><p>{esc(v)}</p></div>",
                       unsafe_allow_html=True)
    st.write("")


ZCFG = {z: st.column_config.ProgressColumn(z, min_value=0, max_value=1, format="percent") for z in ZONES}


def render(p, T, lg):
    S = p["sp_scouting"]
    D, F = flat(S["deliverers"]), flat(S["finishers"])
    c = st.columns(3)
    tf = c[0].selectbox("Team", ["All teams"] + sorted(t["team"] for t in p["table"]), key="sps_team")
    da = c[1].selectbox("Delivery archetype", ["All"] + list(S["del_defs"]), key="sps_da")
    fa = c[2].selectbox("Finishing archetype", ["All"] + list(S["fin_defs"]), key="sps_fa")
    Df = D if tf == "All teams" else D[D.team == tf]
    Ff = F if tf == "All teams" else F[F.team == tf]
    if da != "All":
        Df = Df[Df.arch == da]
    if fa != "All":
        Ff = Ff[Ff.arch == fa]
    defs = pd.DataFrame([{"kind": "delivery", "archetype": k, "definition": v} for k, v in S["del_defs"].items()] +
                        [{"kind": "finishing", "archetype": k, "definition": v} for k, v in S["fin_defs"].items()])
    exports.bar("spscout", f"{p['name']} set-piece scouting{'' if tf == 'All teams' else ' ' + tf}",
                {"Deliverers": Df, "Finishers": Ff, "Definitions": defs},
                {"deliverers": Df.to_dict("records"), "finishers": Ff.to_dict("records")}, None, T, lg)
    heading("Set-piece scouting", "Delivery, finishing and heading archetypes. Fixed rules, so an archetype means the same in "
            "every league.")
    if tf != "All teams" and tf in S["team_mix"]:
        mix = S["team_mix"][tf]
        st.markdown(f"**{tf}: archetype mix** · " + " · ".join(
            f"{k}: " + ", ".join(f"{a} {n}" for a, n in v.items()) for k, v in mix.items()))
    st.markdown("#### Delivery archetypes")
    cards(S["del_defs"], (D if tf == "All teams" else D[D.team == tf]).arch.value_counts().to_dict() if len(D) else {})
    cols = ["player", "team", "arch", "n", "corners", "inswing", "short", "long_throws", "wide_fk"] + ZONES + \
           ["xg_per", "xg_vs_exp100", "rd", "quality_pct", "goals"]
    st.dataframe(Df[[c_ for c_ in cols if c_ in Df]], hide_index=True, width="stretch", height=420, column_config={
        "player": "Player", "team": "Team", "arch": "Archetype", "n": "Deliveries", "corners": "Corners",
        "inswing": st.column_config.NumberColumn("Inswing", format="percent"), "short": st.column_config.NumberColumn("Short", format="percent"),
        "long_throws": "Long throws", "wide_fk": "Wide FKs", **ZCFG,
        "xg_per": st.column_config.NumberColumn("xG / delivery", format="%.3f"),
        "xg_vs_exp100": st.column_config.NumberColumn("xG vs exp. /100", format="%.2f"),
        "rd": st.column_config.NumberColumn("Reach danger", format="percent"),
        "quality_pct": st.column_config.ProgressColumn("Quality pct", min_value=0, max_value=100, format="%d"), "goals": "Goals"})
    st.caption("xG vs expected: xG per delivery minus the league average for the same delivery option, per 100 deliveries. "
               "Zones are shares of direct corners.")
    st.markdown("#### Finishing and heading archetypes")
    cards(S["fin_defs"], (F if tf == "All teams" else F[F.team == tf]).arch.value_counts().to_dict() if len(F) else {})
    cols = ["player", "team", "arch", "att_contacts", "def_contacts", "shots", "headers", "xg", "goals", "aerial", "height"] + ZONES
    st.dataframe(Ff[[c_ for c_ in cols if c_ in Ff]], hide_index=True, width="stretch", height=460, column_config={
        "player": "Player", "team": "Team", "arch": "Archetype", "att_contacts": "Att. first contacts",
        "def_contacts": "Def. first contacts", "shots": "SP shots", "headers": "Headers",
        "xg": st.column_config.NumberColumn("SP xG", format="%.2f"), "goals": "Goals",
        "aerial": st.column_config.NumberColumn("Aerial win", format="percent"), "height": st.column_config.NumberColumn("cm", format="%d"),
        **ZCFG})
    st.caption("First contact = the first touch within 6 seconds of a direct delivery (corner, wide or central free kick, long "
               "throw). Aerial win rate from IMPECT aerial duels (StatsBomb when missing).")
