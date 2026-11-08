import pandas as pd
import streamlit as st

from .. import exports
from .common import heading, team_pick
from .setpieces import CFG, OPT_CFG, RSG, group_table, option_table


def league_table(p):
    rows = []
    for t in p["table"]:
        T = p["setpieces"]["teams"].get(t["team"], {})
        f_, a_ = T.get("for_") or {}, T.get("against") or {}
        gk = (T.get("options_for") or {}).get("Goal kick") or []
        tot = sum(o[1] for o in gk) or 1
        rows.append({"Team": t["team"], "GK short": sum(o[1] for o in gk if o[0].startswith("Short")) / tot,
                     "GK retention": (f_.get("Goal kick") or {}).get("ret"), "GK reach danger": (f_.get("Goal kick") or {}).get("rd"),
                     "Opp GK retention": (a_.get("Goal kick") or {}).get("ret"),
                     "Throw-in retention": (f_.get("Throw-in") or {}).get("ret"), "Kick-off retention": (f_.get("Kick-off") or {}).get("ret")})
    return pd.DataFrame(rows).sort_values("GK short", ascending=False)


def render(p, T, lg):
    team = team_pick(p, "rs_team")
    S = p["setpieces"]
    t = S["teams"].get(team, {})
    f_, a_ = group_table(RSG, t.get("for_") or {}, S["league"]), group_table(RSG, t.get("against") or {}, S["league"])
    opts = option_table(t.get("options_for") or {}, S["options"], RSG)
    opts_a = option_table(t.get("options_against") or {}, S["options"], RSG)
    lgt = league_table(p)
    exports.bar("rs", f"{team} restarts", {"Own restarts": f_, "Opponent restarts": a_, "Options for": opts,
                                            "Options against": opts_a, "League build-up": lgt},
                {"team": team, **t}, None, T, lg)
    heading(f"Restart report: {team}", "goal kicks, throw-ins, kick-offs and own-half free kicks: how they restart and how "
            "they are pressed")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Own restarts** (retention = still in possession at the end of the window)")
        st.dataframe(f_, hide_index=True, width="stretch", column_config=CFG)
    with c2:
        st.markdown("**Opponent restarts against them** (low opponent retention = effective press)")
        st.dataframe(a_, hide_index=True, width="stretch", column_config=CFG)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Restart menu**")
        st.dataframe(opts, hide_index=True, width="stretch", height=520, column_config=OPT_CFG)
    with c2:
        st.markdown("**League: build-up from goal kicks**")
        st.dataframe(lgt, hide_index=True, width="stretch", height=520,
                     column_config={k: st.column_config.NumberColumn(format="percent") for k in lgt.columns if k != "Team"})
