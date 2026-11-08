import pandas as pd
import streamlit as st

from .. import exports
from ..analytics import rows_of
from ..charts import fig_match_numbers, fig_momentum, fig_race, fig_shots
from .common import esc, pick, show

PLAYER_COLS = ["Player", "Position", "Min", "xD added", "xD received", "xD won", "xG", "Shots", "Goals", "Rating"]


def render(p, T, lg):
    M = [m for m in p["matches"] if m.get("status") == "played" and m.get("post")][::-1]
    if not M:
        st.info("No played matches.")
        return
    teams = ["All teams"] + sorted(t["team"] for t in p["table"])
    c1, c2 = st.columns([1, 2.4])
    tf = c1.selectbox("Team", teams, key="post_team")
    ML = M if tf == "All teams" else [m for m in M if tf in (m["home"], m["away"])]
    by = {str(m["id"]): m for m in ML}
    with c2:
        sid = pick("Match", list(by), "post_pick", fmt=lambda i: (
            f"{(by[i]['date'] or '')[:10]} · {by[i]['home']} {by[i]['hg']}-{by[i]['ag']} {by[i]['away']} · "
            f"xG {by[i]['post']['stats'][0]['xg']:.2f}-{by[i]['post']['stats'][1]['xg']:.2f}"))
    m = by[sid]
    P = m["post"]
    team = lambda i: m["away"] if i else m["home"]  # noqa: E731
    sheets = {
        "Stats": [{"metric": k, m["home"]: P["stats"][0][k], m["away"]: P["stats"][1][k]} for k in P["stats"][0]],
        "Shots": [dict(team=team(r["side"]), **r) for r in rows_of(P["shots"], ["side", "minute", "x", "y", "xg", "goal", "player", "body_part", "set_piece", "xgot", "type"])],
        "Players": [dict(team=team(i), **r) for i in (0, 1) for r in rows_of(P["players"][i], [c.lower().replace(" ", "_") for c in PLAYER_COLS])],
        "Set pieces": [dict(team=team(r["side"]), **r) for r in rows_of(P["setpieces"], ["side", "minute", "type", "option", "taker", "xg", "reached_danger", "goal"])],
        "Momentum": [{"minutes": f"{i * 5}-{i * 5 + 5}", m["home"]: v[0], m["away"]: v[1]} for i, v in enumerate(P["momentum"])],
    }
    exports.bar("post", f"{m['home']} {m['hg']}-{m['ag']} {m['away']}", sheets, m,
                lambda: [fig_match_numbers(m, T), fig_race(m, T), fig_momentum(m, T), fig_shots(m, 0, T), fig_shots(m, 1, T)],
                T, lg)
    a, b = P["stats"]
    st.markdown(f"<div class='wa-eyebrow'>{esc(m['md'] or '')} · {esc((m['date'] or '')[:10])} · "
                f"{esc(' v '.join(f or '?' for f in (P.get('formations') or [None, None])))}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 0.6, 1], vertical_alignment="center")
    c1.markdown(f"<div class='wa-team' style='text-align:right'>{esc(m['home'])}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='wa-score'>{m['hg']} - {m['ag']}</div><div class='wa-muted' style='text-align:center'>"
                f"xG {a['xg']:.2f} - {b['xg']:.2f} · xD {a['xd']:.2f} - {b['xd']:.2f}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='wa-team'>{esc(m['away'])}</div>", unsafe_allow_html=True)
    if P.get("pdf"):
        links = " · ".join(f"[{k.replace('_', ' ')}]({u})" for k, u in P["pdf"].items() if k.endswith(st.session_state.get("theme", "navy")))
        if links:
            st.caption(f"PDF match reports (daily-match-reports agent, open locally): {links}")
    c1, c2 = st.columns([1, 1.15])
    with c1:
        show(fig_match_numbers(m, T))
    with c2:
        show(fig_race(m, T))
        show(fig_momentum(m, T))
    c1, c2 = st.columns(2)
    with c1:
        show(fig_shots(m, 0, T))
    with c2:
        show(fig_shots(m, 1, T))
    cfg = {"xD added": st.column_config.NumberColumn(format="%.3f"), "xD received": st.column_config.NumberColumn(format="%.2f"),
           "xD won": st.column_config.NumberColumn(format="%.3f"), "xG": st.column_config.NumberColumn(format="%.2f"),
           "Min": st.column_config.NumberColumn(format="%d"),
           "Rating": st.column_config.ProgressColumn("Rating (M5)", min_value=0, max_value=10, format="%.1f")}
    st.caption("Players sorted by xDanger added. Rating: WA Model 5, 0 to 10, 6.5 = position average.")
    c1, c2 = st.columns(2)
    for col, i in ((c1, 0), (c2, 1)):
        with col:
            st.markdown(f"**{team(i)}**")
            st.dataframe(pd.DataFrame(P["players"][i], columns=PLAYER_COLS), hide_index=True, width="stretch", column_config=cfg)
    st.markdown("**Set pieces in this match** (xG in the 30-second window after each restart)")
    sp = pd.DataFrame(sheets["Set pieces"]).drop(columns=["side"], errors="ignore")
    st.dataframe(sp, hide_index=True, width="stretch", column_config={"xg": st.column_config.NumberColumn("xG", format="%.3f")})
