import pandas as pd
import streamlit as st

from .. import exports
from ..charts import fig_goal_mouth
from .common import heading, show


def render(p, T, lg):
    P = p["penalties"]
    if not P["list"]:
        st.info("No penalties yet.")
        return
    teams = ["All teams"] + sorted(t["team"] for t in p["table"])
    tf = st.selectbox("Team", teams, key="pen_team")
    L = P["list"] if tf == "All teams" else [x for x in P["list"] if tf in (x["team"], x["opp"])]
    shots = P["list"] if tf == "All teams" else [x for x in P["list"] if x["team"] == tf]
    lst = pd.DataFrame(L)[::-1]
    takers = pd.DataFrame(P["takers"], columns=["Taker", "Team", "Taken", "Scored", "Left", "Centre", "Right", "High"])
    takers["Conversion"] = takers.Scored / takers.Taken
    keepers = pd.DataFrame(P["keepers"], columns=["Keeper", "Team", "Faced", "Conceded", "Saved"])
    keepers["Saved"] = keepers.Saved.clip(lower=0)
    tm = pd.DataFrame(P["teams"], columns=["Team", "Won", "Conceded", "Scored", "Goals against"]).sort_values("Won", ascending=False)
    if tf != "All teams":
        takers, keepers, tm = takers[takers.Team == tf], keepers[keepers.Team == tf], tm[tm.Team == tf]
    title = f"Penalty placement{': ' + tf if tf != 'All teams' else ''}"
    exports.bar("pen", f"{p['name']} penalties{' ' + tf if tf != 'All teams' else ''}",
                {"Penalties": lst, "Takers": takers, "Keepers": keepers, "Teams": tm}, P,
                lambda: [fig_goal_mouth(shots, T, title)], T, lg)
    heading("Penalty report", f"{len(P['list'])} penalties · {P['conv']:.0%} scored")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        show(fig_goal_mouth(shots, T, title))
        st.dataframe(lst[["date", "minute", "taker", "team", "keeper", "option", "goal"]], hide_index=True, width="stretch",
                     height=300, column_config={"goal": st.column_config.CheckboxColumn("Scored")})
    with c2:
        st.markdown("**Takers** (placement from the taker's view; high = upper half)")
        st.dataframe(takers, hide_index=True, width="stretch", height=300,
                     column_config={"Conversion": st.column_config.NumberColumn(format="percent")})
        a, b = st.columns(2)
        with a:
            st.markdown("**Keepers**")
            st.dataframe(keepers, hide_index=True, width="stretch")
        with b:
            st.markdown("**Teams**")
            st.dataframe(tm, hide_index=True, width="stretch")
