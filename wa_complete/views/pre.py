import pandas as pd
import streamlit as st

from .. import exports
from ..analytics import rows_of, team_style
from ..charts import fig_radar
from .common import esc, form_html, num, pct, pick, prob_bar, short, show

RANKS = [("xG for", "xg_f"), ("xG against", "xg_a"), ("xDanger for", "xd_f"), ("xDanger against", "xd_a"),
         ("Set-piece xG for", "sp_xg_f"), ("Set-piece xG against", "sp_xg_a")]


def style_fig(p, x, T):
    keys, raw, z = team_style(p)
    ser = [dict(name=t, color=c, z=[None if pd.isna(z.loc[t, k]) else float(z.loc[t, k]) for k in keys])
           for t, c in ((x["home"], T["accent"]), (x["away"], T["blue"])) if t in z.index]
    return fig_radar(keys, ser, T, "Style radar", f"Deviation from the {p['name']} team average (dashed ring); "
                     "'prevented' metrics are flipped so outside is always better", avg_label="league avg")


def card(c, n, col, T):
    if c.get("no_data"):
        st.info(f"{c['team']}: no matches yet")
        return
    st.markdown(f"<div style='border-top:3px solid {col};padding-top:6px'><span class='wa-team'>{esc(c['team'])}</span><br>"
                f"<span class='wa-muted'>#{c['pos']} · {c['pts']} pts · {c['w']}-{c['d']}-{c['l']} · goals {c['gf']}:{c['ga']}</span> "
                f"{form_html(c['form'])}</div>", unsafe_allow_html=True)
    rk = pd.DataFrame([dict(Metric=l, Value=c[k], Rank=c["ranks"][k], Strength=(n - c["ranks"][k] + 1) / n) for l, k in RANKS])
    st.dataframe(rk, hide_index=True, width="stretch", column_config={
        "Value": st.column_config.NumberColumn(format="%.2f"),
        "Rank": st.column_config.NumberColumn(format="#%d", width="small"),
        "Strength": st.column_config.ProgressColumn("League rank", min_value=0, max_value=1, format=" ")})
    st.markdown("**Last five**")
    st.dataframe(pd.DataFrame(rows_of(c["last5"], ["Date", "Opponent", "Venue", "GF", "GA", "xG", "xGA", "Res"])),
                 hide_index=True, width="stretch")
    st.markdown("**Key xDanger creators**")
    st.dataframe(pd.DataFrame(rows_of(c["key_players"], ["Player", "Position", "xD added p90", "Minutes"])),
                 hide_index=True, width="stretch")
    mv = f"€{c['mv_eur'] / 1e6:.1f}m" if c.get("mv_eur") else "·"
    kv = [("Corners per match", num(c.get("corners_pm"), 1)), ("Main corner taker", c.get("corner_taker") or "·"),
          ("Preferred deliveries", ", ".join(f"{o} {s:.0%}" for o, s in c.get("corner_pref") or []) or "·"),
          ("Set-piece threats (xG)", ", ".join(f"{a} {b:.2f}" for a, b in c.get("sp_threats") or []) or "·"),
          ("Penalty taker", c.get("pen_taker") or "·"), ("Goal kicks played short", pct(c.get("gk_short"))),
          ("Formation", c.get("formation") or "·"), ("Market value (Transfermarkt)", mv),
          ("Average age (270+ min)", num(c.get("avg_age"), 1)),
          ("Top speed avg (SkillCorner)", f"{c['top_speed']:.1f} km/h" if c.get("top_speed") else "·"),
          ("High-intensity m p90 (SkillCorner)", num(c.get("hi_dist"), 0)), ("OBV p90 avg (StatsBomb)", num(c.get("obv"), 3)),
          ("WTV p90 avg (Opta)", num(c.get("wtv"), 3))]
    st.dataframe(pd.DataFrame(kv, columns=["Set pieces, restarts and squad", ""]), hide_index=True, width="stretch")


def render(p, T, lg):
    P = p.get("previews") or []
    if not P:
        st.info("No upcoming fixtures in the data.")
        return
    by = {str(x["id"]): x for x in P}
    sid = pick("Fixture", list(by), "pre_pick",
               fmt=lambda i: f"{(by[i]['date'] or '')[:16].replace('T', ' ')} · {by[i]['home']} v {by[i]['away']} "
                             f"({by[i]['prob'][0]:.0%} / {by[i]['prob'][1]:.0%} / {by[i]['prob'][2]:.0%})")
    x = by[sid]
    h, a = x["h"], x["a"]
    flat = lambda c: {**{k: v for k, v in c.items() if not isinstance(v, (list, dict))}, **{f"rank_{k}": v for k, v in (c.get("ranks") or {}).items()}}  # noqa: E731
    keys, raw, z = team_style(p)
    style_rows = [{"metric": k, x["home"]: raw.loc[x["home"], k] if x["home"] in raw.index else None,
                   x["home"] + " z": z.loc[x["home"], k] if x["home"] in z.index else None,
                   x["away"]: raw.loc[x["away"], k] if x["away"] in raw.index else None,
                   x["away"] + " z": z.loc[x["away"], k] if x["away"] in z.index else None} for k in keys]
    sheets = {"Summary": [dict(date=x["date"], matchday=x["md"], home=x["home"], away=x["away"], exp_home=x["exp"][0],
                               exp_away=x["exp"][1], p_home=x["prob"][0], p_draw=x["prob"][1], p_away=x["prob"][2],
                               set_piece_edge_home=x["sp_edge"])],
              "Teams": [flat(h), flat(a)],
              "Last five": [dict(team=c["team"], **r) for c in (h, a) if not c.get("no_data")
                            for r in rows_of(c["last5"], ["date", "opponent", "venue", "gf", "ga", "xg_f", "xg_a", "result"])],
              "Key players": [dict(team=c["team"], **r) for c in (h, a) if not c.get("no_data")
                              for r in rows_of(c["key_players"], ["player", "position", "xd_added_p90", "minutes"])],
              "Style radar": style_rows}
    exports.bar("pre", f"{x['home']} v {x['away']} preview", sheets, x, lambda: [style_fig(p, x, T)], T, lg)

    st.markdown(f"<div class='wa-eyebrow'>{esc(x['md'] or '')} · {esc((x['date'] or '')[:16].replace('T', ' '))} UTC</div>",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 0.7, 1], vertical_alignment="center")
    c1.markdown(f"<div class='wa-team' style='text-align:right'>{esc(x['home'])}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='wa-score' style='font-size:28px'>{x['exp'][0]:.2f} - {x['exp'][1]:.2f}</div>"
                "<div class='wa-muted' style='text-align:center'>expected goals</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='wa-team'>{esc(x['away'])}</div>", unsafe_allow_html=True)
    st.markdown(prob_bar(x["prob"], T), unsafe_allow_html=True)
    h2h = ", ".join(f"{m[0]} ({'home' if m[1] == 'H' else 'away'}) {m[2]}-{m[3]}" for m in x["h2h"]) or "no earlier meeting this season"
    st.caption("Poisson model on a 60/40 blend of non-penalty xG and xDanger (scaled to xG), for and against, with the "
               f"league's home and away rates. Head to head: {h2h}.")
    if not h.get("no_data") and not a.get("no_data"):
        def who(x1, x2, low=False):
            return short(x["home"]) if ((x1 < x2) if low else (x1 > x2)) else short(x["away"])
        st.markdown("**Where the edges are**  \n"
                    f"- Open-play threat (xDanger for): {who(h['xd_f'], a['xd_f'])}\n"
                    f"- Defensive solidity (xDanger against): {who(h['xd_a'], a['xd_a'], True)}\n"
                    f"- Set-piece threat: {who(h['sp_xg_f'], a['sp_xg_f'])}\n"
                    f"- Set-piece defending: {who(h['sp_xg_a'], a['sp_xg_a'], True)}\n"
                    f"- Set-piece balance: {short(x['home']) if x['sp_edge'] > 0 else short(x['away'])} "
                    f"({abs(x['sp_edge']):.3f} set-piece xG per match net)")
    l, mid, r = st.columns([0.15, 1, 0.15])
    with mid:
        show(style_fig(p, x, T))
    n = len(p["table"])
    c1, c2 = st.columns(2)
    with c1:
        card(h, n, T["accent"], T)
    with c2:
        card(a, n, T["blue"], T)
