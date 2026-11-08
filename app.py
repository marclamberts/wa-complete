"""WA Complete: Waltzing Analytics Match Hub 26-27 in Streamlit.

    streamlit run app.py

Ten leagues (Eredivisie, Jupiler Pro League, Bundesliga, 2. Bundesliga, 3. Liga, five Regionalligen), pre- and post-match
reports, set-piece, restart and penalty reports, scouting with pizza and deviation radar, set-piece scouting archetypes,
all driven by the xDanger models; navy or fog; PDF, Excel, CSV and JSON for every view. Data comes from the WA Match Hub
daily agent (see wa_complete/data.py).
"""
import streamlit as st

from wa_complete import data, style
from wa_complete.views import PAGES

st.set_page_config(page_title="WA Complete · Match Hub 26-27", page_icon="⚽", layout="wide")

qp = st.query_params
if "theme" not in st.session_state:
    st.session_state.theme = qp.get("theme", "navy") if qp.get("theme") in style.THEMES else "navy"

leagues = data.available()
with st.sidebar:
    st.markdown("<div class='wa-eyebrow'>Waltzing Analytics · xDanger</div>", unsafe_allow_html=True)
    st.markdown("## Match Hub 26-27")
    theme = st.segmented_control("Style", ["navy", "fog"], default=st.session_state.theme, key="theme_ctl",
                                 format_func=str.title) or st.session_state.theme
    if not leagues:
        st.error("No league data found. Run the WA Match Hub agent, or point WA_HUB_DATA at its exports folder.")
        st.stop()
    keys = [k for k, _, _ in leagues]
    names = {k: f"{g} · {n}" for k, n, g in leagues}
    want = qp.get("league", "NED1")
    league = st.selectbox("League", keys, index=keys.index(want) if want in keys else 0, format_func=names.get)
    page_keys = [k for k, _, _ in PAGES]
    want_p = qp.get("page", "post")
    page = st.radio("Report", page_keys, index=page_keys.index(want_p) if want_p in page_keys else 0,
                    format_func=dict((k, lab) for k, lab, _ in PAGES).get)

T = style.THEMES[theme]
if theme != st.session_state.theme or style.set_streamlit_theme(theme):
    st.session_state.theme = theme
    qp["theme"] = theme
    st.rerun()
style.inject_css(T)
style.mpl(T)

if qp.get("league") != league or qp.get("page") != page:
    if qp.get("page") != page or qp.get("league") != league:
        qp.pop("sel", None)
        qp.pop("player", None)
    qp["league"], qp["page"] = league, page

p = data.load(league)
lg = {"key": league, "name": p["name"]}
with st.sidebar:
    st.caption(f"Data updated {(p.get('updated') or '').replace('T', ' ')} · {p['n_played']} matches\n\n"
               "IMPECT · Opta · StatsBomb · SkillCorner · Transfermarkt\n\n"
               f"Source: `{data.root()}`")

module = dict((k, m) for k, _, m in PAGES)[page]
module.render(p, T, lg)
