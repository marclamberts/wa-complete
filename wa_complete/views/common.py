"""Small shared pieces for the views."""
from __future__ import annotations

import html

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ..charts import short  # noqa: F401  (re-exported)


def esc(s):
    return html.escape(str(s if s is not None else ""))


def show(fig):
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def heading(title, sub=""):
    st.markdown(f"### {esc(title)}")
    if sub:
        st.markdown(f"<div class='wa-sub'>{esc(sub)}</div>", unsafe_allow_html=True)


def form_html(s):
    return "<span class='wa-form'>" + "".join(f"<span class='wa-{c}'>{c}</span>" for c in (s or "")) + "</span>"


def prob_bar(prob, T):
    h, d, a = prob
    return (f"<div class='wa-prob'><div style='width:{h * 100}%;background:{T['accent']}'>{h:.0%}</div>"
            f"<div style='width:{d * 100}%;background:{T['grey']};color:{T['ink']}'>{d:.0%}</div>"
            f"<div style='width:{a * 100}%;background:{T['blue']}'>{a:.0%}</div></div>")


def pct(v):
    return "·" if v is None or pd.isna(v) else f"{v:.0%}"


def num(v, d=2):
    return "·" if v is None or (isinstance(v, float) and pd.isna(v)) else f"{v:.{d}f}"


def qp_get(name, default=None):
    return st.query_params.get(name, default)


def qp_set(**kw):
    for k, v in kw.items():
        if v is None:
            st.query_params.pop(k, None)
        else:
            st.query_params[k] = str(v)


def pick(label, options, key, default_value=None, fmt=None):
    """Selectbox whose choice is mirrored in the URL (?sel=...), so views can be bookmarked."""
    values = list(options)
    want = qp_get("sel", default_value)
    idx = next((i for i, v in enumerate(values) if str(v) == str(want)), 0)
    choice = st.selectbox(label, values, index=idx if values else None, key=key, format_func=fmt or str)
    if choice is not None and str(choice) != str(qp_get("sel")):
        qp_set(sel=choice)
    return choice


def team_pick(p, key, label="Team"):
    teams = sorted(t["team"] for t in p["table"])
    return pick(label, teams, key)
