import pandas as pd
import streamlit as st

from .. import exports
from ..charts import fig_xd_scatter
from .common import heading, show


def render(p, T, lg):
    tb = pd.DataFrame(p["table"])
    cols = ["pos", "team", "p", "w", "d", "l", "gf", "ga", "gd", "pts", "form", "xg_f", "xg_a", "npxg_f", "npxg_a",
            "xd_f", "xd_a", "xd_diff", "sp_xg_f", "sp_xg_a"]
    tb = tb[[c for c in cols if c in tb]]
    exports.bar("league", f"{p['name']} table", {"Table": tb}, p["table"],
                lambda: [fig_xd_scatter(p["table"], T, p["name"])], T, lg)
    src = ", ".join(k for k, v in (p.get("sources") or {}).items() if v)
    heading(p["name"], f"{p['n_played']} matches · {p['n_actions']:,} scored actions · sources: {src}")
    c1, c2 = st.columns([1.55, 1])
    with c1:
        st.markdown("**Table with xDanger** (per match; xDanger = positive in-possession xDanger added)")
        st.dataframe(tb, hide_index=True, width="stretch", height=min(38 * len(tb) + 40, 760), column_config={
            "pos": st.column_config.NumberColumn("#", width="small"), "team": "Team", "p": "P", "w": "W", "d": "D",
            "l": "L", "gf": "GF", "ga": "GA", "gd": "GD", "pts": "Pts", "form": "Form",
            "xg_f": st.column_config.NumberColumn("xG", format="%.2f"), "xg_a": st.column_config.NumberColumn("xGA", format="%.2f"),
            "npxg_f": st.column_config.NumberColumn("npxG", format="%.2f"), "npxg_a": st.column_config.NumberColumn("npxGA", format="%.2f"),
            "xd_f": st.column_config.NumberColumn("xD", format="%.2f"), "xd_a": st.column_config.NumberColumn("xDA", format="%.2f"),
            "xd_diff": st.column_config.NumberColumn("xD +/-", format="%.2f"),
            "sp_xg_f": st.column_config.NumberColumn("SP xG", format="%.3f"), "sp_xg_a": st.column_config.NumberColumn("SP xGA", format="%.3f")})
    with c2:
        show(fig_xd_scatter(p["table"], T, p["name"]))
