import pandas as pd
import streamlit as st

from .. import exports
from ..analytics import MIN_POOL, pos_pool, profile_rows, scouting_frame
from ..charts import fig_pizza, fig_radar
from .common import esc, heading, num, qp_get, qp_set, show

COLS = [("name", "Player", None), ("team", "Team", None), ("age", "Age", "%d"), ("pos_group", "Pos", None),
        ("minutes", "Min", "%d"), ("xd_added_p90", "xD added", "%.3f"), ("pct_xd_added_p90", "xD added pct", "pct"),
        ("xd_received_p90", "xD received", "%.2f"), ("xd_won_p90", "xD won", "%.3f"), ("xd_denied_p90", "xD denied", "%.3f"),
        ("xg_p90", "xG", "%.2f"), ("net_p90", "Net value (M3)", "%.3f"), ("pae_100", "xPass +/100 (M4)", "%.1f"),
        ("wa_rating", "WA rating (M5)", "%.2f"), ("wa_composite", "WA comp.", "%.1f"), ("opta_wtv_p90", "WTV (Opta)", "%.3f"),
        ("sb_obv_90", "OBV (SB)", "%.3f"), ("sc_psv99", "Top speed (SC)", "%.1f"),
        ("sc_hi_distance_full_all_p90", "HI m (SC)", "%d"), ("tm_market_value_eur", "Value € (TM)", "eur"),
        ("contract_until", "Contract", None), ("height", "cm", "%d"), ("sp_del", "SP delivery", None),
        ("sp_fin", "SP finishing", None), ("tm_profile_url", "TM", "link")]


def figs_for(df, pl, cmp, T, league):
    rows = profile_rows(df, pl)
    pool = pos_pool(df, pl.pos_group)
    pz = fig_pizza(rows, T, pl["name"], f"{pl.team} · {pl.pos_group} · percentile against {len(pool)} {pl.pos_group} "
                   f"players in {league} with {MIN_POOL}+ minutes")
    ok = [r for r in rows if r["z"] is not None]
    series = [dict(name=pl["name"], color=T["accent"], z=[r["z"] for r in ok])]
    if cmp is not None:
        cm = {r["key"]: r for r in profile_rows(df, cmp)}
        series.append(dict(name=cmp["name"], color=T["blue"], z=[(cm.get(r["key"]) or {}).get("z") for r in ok]))
    rd = fig_radar([r["metric"] for r in ok], series, T, "Deviation radar",
                   f"Standard deviations from the {pl.pos_group} average (dashed ring); outside = above average",
                   avg_label=f"{pl.pos_group} avg")
    return rows, pz, rd


def render(p, T, lg):
    df = scouting_frame(p)
    c = st.columns([1.6, 1, 0.8, 0.8])
    q = c[0].text_input("Search", placeholder="player or team", key="sc_q")
    pos = c[1].selectbox("Position", ["All"] + sorted(df.pos_group.dropna().unique()), key="sc_pos")
    max_age = c[2].number_input("Max age", 15, 45, 45, key="sc_age")
    min_min = c[3].number_input("Min minutes", 0, 5000, 300, step=90, key="sc_min")
    f = df[(df.minutes.fillna(0) >= min_min) & (df.age.fillna(99) <= max_age if max_age < 45 else True)]
    if pos != "All":
        f = f[f.pos_group == pos]
    if q:
        f = f[(f.name.fillna("") + " " + f.team.fillna("")).str.lower().str.contains(q.lower(), regex=False)]
    f = f.sort_values("xd_added_p90", ascending=False)

    sel_name = qp_get("player")
    pl = df[df.name == sel_name].iloc[0] if sel_name in set(df.name) else None
    cmp_name = st.session_state.get("sc_cmp") or None
    cmp = df[df.name == cmp_name].iloc[0] if pl is not None and cmp_name in set(df.name) and cmp_name != pl["name"] else None
    sheets = {"Players": f}
    if pl is not None:
        sheets["Profile"] = pd.DataFrame(profile_rows(df, pl)).drop(columns=["key"])
    exports.bar("scout", f"{pl['name']} profile" if pl is not None else f"{p['name']} scouting", sheets,
                (pl.to_dict() if pl is not None else f.to_dict("records")),
                (lambda: list(figs_for(df, pl, cmp, T, p["name"])[1:])) if pl is not None else None, T, lg)
    heading("Scouting", "xDanger per 90 with percentiles inside the position group, Models 3 to 5, and Opta, StatsBomb, "
            "SkillCorner and Transfermarkt from the WA Scouting DB. Select a row for the pizza and deviation radar.")

    if pl is not None:
        with st.container(border=True):
            a, b, c_ = st.columns([2.2, 1.6, 0.5], vertical_alignment="bottom")
            mv = f"€{pl.tm_market_value_eur / 1e6:.1f}m" if pd.notna(pl.get("tm_market_value_eur")) else "·"
            a.markdown(f"<span class='wa-team' style='font-size:24px'>{esc(pl['name'])}</span> "
                       f"<span class='wa-muted'>{esc(pl.team)} · {esc(pl.pos_group)}</span><br><span class='wa-muted'>"
                       f"Age <b>{num(pl.age, 0)}</b> · Minutes <b>{num(pl.minutes, 0)}</b> · Foot <b>{esc(pl.get('foot') or '·')}</b> · "
                       f"Height <b>{num(pl.get('height'), 0)}</b> · Value <b>{mv}</b> · Contract <b>{esc(pl.get('contract_until') or '·')}</b>"
                       f"<br>SP delivery <b>{esc(pl.get('sp_del') or '·')}</b> · SP finishing <b>{esc(pl.get('sp_fin') or '·')}</b></span>",
                       unsafe_allow_html=True)
            others = df[(df.pos_group == pl.pos_group) & (df.name != pl["name"])].sort_values("minutes", ascending=False)
            b.selectbox("Compare on the radar", [""] + list(others.name), key="sc_cmp",
                        format_func=lambda v: v or "Position average only")
            if c_.button("Close", key="sc_close"):
                qp_set(player=None)
                st.session_state.pop("sc_cmp", None)
                st.rerun()
            rows, pz, rd = figs_for(df, pl, cmp, T, p["name"])
            l, r = st.columns(2)
            with l:
                show(pz)
            with r:
                show(rd)

    view = f[[k for k, _, _ in COLS if k in f]].rename(columns={k: lab for k, lab, _ in COLS})
    cfg = {}
    for k, lab, fmt in COLS:
        if fmt == "pct":
            cfg[lab] = st.column_config.ProgressColumn(lab, min_value=0, max_value=100, format="%d")
        elif fmt == "eur":
            cfg[lab] = st.column_config.NumberColumn(lab, format="compact")
        elif fmt == "link":
            cfg[lab] = st.column_config.LinkColumn(lab, display_text="profile")
        elif fmt:
            cfg[lab] = st.column_config.NumberColumn(lab, format=fmt)
    st.caption(f"{len(f)} players")
    ev = st.dataframe(view, hide_index=True, width="stretch", height=560, column_config=cfg, on_select="rerun",
                      selection_mode="single-row", key="sc_table")
    rows_sel = (ev.selection.rows if ev and getattr(ev, "selection", None) else [])
    if rows_sel:
        name = view.iloc[rows_sel[0]]["Player"]
        if name != sel_name:
            qp_set(player=name)
            st.session_state.pop("sc_cmp", None)
            st.rerun()
