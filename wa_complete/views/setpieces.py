import pandas as pd
import streamlit as st

from .. import exports
from ..analytics import rows_of
from ..charts import fig_corner_map
from .common import heading, show, team_pick

SPG = ["Corner", "Short corner", "Direct free kick", "Wide free kick", "Central free kick", "Long throw", "Penalty"]
RSG = ["Goal kick", "Throw-in", "Kick-off", "Own-half free kick"]


def group_table(groups, mine, lg):
    rows = []
    for g in groups:
        x, l = mine.get(g), lg.get(g, {})
        if not x:
            continue
        rows.append({"Type": g, "n": x["n"], "Per match": x["pm"], "xG / restart": x["xg"], "League xG": l.get("xg"),
                     "Reach danger": x["rd"], "League danger": l.get("rd"), "Retention": x["ret"],
                     "League retention": l.get("ret"), "Shots": x["shots"], "Goals": x["goals"],
                     "Goal against": x["ga"], "Setup s": x["setup"]})
    return pd.DataFrame(rows)


CFG = {"Per match": st.column_config.NumberColumn(format="%.2f"), "xG / restart": st.column_config.NumberColumn(format="%.3f"),
       "League xG": st.column_config.NumberColumn(format="%.3f"),
       **{k: st.column_config.NumberColumn(format="percent") for k in ("Reach danger", "League danger", "Retention", "League retention")},
       "Goal against": st.column_config.NumberColumn(format="percent"), "Setup s": st.column_config.NumberColumn(format="%.1f")}


def option_table(opts, lg_opts, groups):
    rows = []
    for g in groups:
        lst = opts.get(g) or []
        tot = sum(o[1] for o in lst) or 1
        ltot = sum(o[1] for o in lg_opts.get(g) or []) or 1
        lmap = {o[0]: o for o in lg_opts.get(g) or []}
        for o in sorted(lst, key=lambda o: -o[1]):
            rows.append({"Type": g, "Option": o[0], "n": o[1], "Share": o[1] / tot,
                         "League share": (lmap.get(o[0], [None, 0])[1] or 0) / ltot, "xG": o[2], "Reach danger": o[3],
                         "Retention": o[4], "Goal against": o[5]})
    return pd.DataFrame(rows)


OPT_CFG = {**{k: st.column_config.NumberColumn(format="percent") for k in ("Share", "League share", "Reach danger", "Retention", "Goal against")},
           "xG": st.column_config.NumberColumn(format="%.3f")}


def render(p, T, lg):
    team = team_pick(p, "sp_team")
    S = p["setpieces"]
    t = S["teams"].get(team, {})
    f_, a_ = group_table(SPG, t.get("for_") or {}, S["league"]), group_table(SPG, t.get("against") or {}, S["league"])
    opts = option_table(t.get("options_for") or {}, S["options"], SPG)
    opts_a = option_table(t.get("options_against") or {}, S["options"], SPG)
    takers = pd.DataFrame([{"Player": n, **d} for n, d in t.get("takers") or []]).fillna(0)
    targets = pd.DataFrame(rows_of(t.get("targets"), ["Player", "Shots", "Headers", "xG", "Goals"]))
    lgt = pd.DataFrame(p["table"])[["team", "sp_xg_f", "sp_xg_f_rk", "sp_xg_a", "sp_xg_a_rk"]].sort_values("sp_xg_f", ascending=False)
    sheets = {"For": f_, "Against": a_, "Options for": opts, "Options against": opts_a, "Takers": takers, "Targets": targets,
              "Corner map for": rows_of(t.get("corner_map"), ["end_x", "end_y_folded", "goal", "xg"]),
              "Corner map against": rows_of(t.get("corner_map_against"), ["end_x", "end_y_folded", "goal", "xg"]),
              "League": lgt}
    figs = lambda: [fig_corner_map(t.get("corner_map"), T, f"{team}: corner deliveries for"),  # noqa: E731
                    fig_corner_map(t.get("corner_map_against"), T, f"{team}: corner deliveries against",
                                   "Where opponents deliver against them")]
    exports.bar("sp", f"{team} set pieces", sheets, {"team": team, **t}, figs, T, lg)
    heading(f"Set-piece report: {team}", f"{t.get('matches', 0)} matches · every restart scored on xDanger, xShot and xG in "
            "its 30-second window, compared with the league")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Attacking set pieces**")
        st.dataframe(f_, hide_index=True, width="stretch", column_config=CFG)
    with c2:
        st.markdown("**Defending set pieces** (what opponents produce against them)")
        st.dataframe(a_, hide_index=True, width="stretch", column_config=CFG)
    c1, c2, c3 = st.columns([1, 1, 1.1])
    with c1:
        show(fig_corner_map(t.get("corner_map"), T, "Corner deliveries for"))
    with c2:
        show(fig_corner_map(t.get("corner_map_against"), T, "Corner deliveries against", "Where opponents deliver against them"))
    with c3:
        st.markdown("**League: set-piece xG per match**")
        st.dataframe(lgt, hide_index=True, width="stretch", height=430, column_config={
            "team": "Team", "sp_xg_f": st.column_config.NumberColumn("For", format="%.3f"), "sp_xg_f_rk": st.column_config.NumberColumn("#", format="%d"),
            "sp_xg_a": st.column_config.NumberColumn("Against", format="%.3f"), "sp_xg_a_rk": st.column_config.NumberColumn("#", format="%d")})
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("**Delivery menu** (share vs league share, xG per restart, reach danger, retention)")
        st.dataframe(opts, hide_index=True, width="stretch", height=480, column_config=OPT_CFG)
    with c2:
        st.markdown("**Takers**")
        st.dataframe(takers, hide_index=True, width="stretch")
        st.markdown("**Targets** (set-piece shots, no penalties)")
        st.dataframe(targets, hide_index=True, width="stretch", column_config={"xG": st.column_config.NumberColumn(format="%.2f")})
