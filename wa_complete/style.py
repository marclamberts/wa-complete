"""Navy and fog: Streamlit theme, page CSS and matplotlib defaults from one palette."""
from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import streamlit as st
from streamlit import config as _cfg

matplotlib.use("Agg")

THEMES = {
    "navy": dict(bg="#14202B", panel="#1C2935", panel2="#22313E", ink="#F2EFE6", muted="#86847E", muted2="#A8A6A0",
                 hair="#384653", accent="#E8794C", blue="#5B8AC9", teal="#1FA88C", gold="#B37F1E", grey="#3C4A57",
                 pitch="#182633", line="#52657A", chip="#2A3A48", base="dark"),
    "fog": dict(bg="#E7ECEE", panel="#F1F4F5", panel2="#FFFFFF", ink="#1A2226", muted="#78888D", muted2="#5E6E73",
                hair="#CBD6D9", accent="#E8794C", blue="#4C7A93", teal="#5E8C6A", gold="#C0902F", grey="#B9C6CA",
                pitch="#DDE5E8", line="#B4C3C7", chip="#DCE4E7", base="light"),
}
SERIF = "Georgia"
SANS = "Helvetica Neue"


def set_streamlit_theme(name: str) -> bool:
    """Point Streamlit's own theme at the palette. Returns True when something changed (caller reruns)."""
    T = THEMES[name]
    opts = {"theme.base": T["base"], "theme.primaryColor": T["accent"], "theme.backgroundColor": T["bg"],
            "theme.secondaryBackgroundColor": T["panel"], "theme.textColor": T["ink"]}
    changed = False
    for k, v in opts.items():
        try:
            if _cfg.get_option(k) != v:
                _cfg.set_option(k, v)
                changed = True
        except Exception:
            pass
    return changed


def inject_css(T: dict):
    st.markdown(f"""<style>
      .stApp {{ background: {T['bg']}; color: {T['ink']}; }}
      [data-testid="stSidebar"] {{ background: {T['panel']}; }}
      h1, h2, h3 {{ font-family: Georgia, 'Times New Roman', serif !important; color: {T['ink']}; }}
      .wa-eyebrow {{ color: {T['accent']}; font-weight: 700; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }}
      .wa-sub {{ color: {T['muted']}; font-size: 12px; margin-top: -6px; }}
      .wa-card {{ background: {T['panel']}; border: 1px solid {T['hair']}; border-radius: 9px; padding: 12px 16px; margin-bottom: 12px; }}
      .wa-score {{ font-family: Georgia, serif; font-size: 34px; font-weight: 700; text-align: center; color: {T['ink']}; }}
      .wa-team {{ font-family: Georgia, serif; font-size: 20px; font-weight: 700; color: {T['ink']}; }}
      .wa-muted {{ color: {T['muted']}; font-size: 12px; }}
      .wa-chip {{ display: inline-block; padding: 1px 8px; border-radius: 10px; background: {T['chip']}; font-size: 11px; font-weight: 700; margin-right: 4px; }}
      .wa-form span {{ display: inline-block; width: 18px; height: 18px; line-height: 18px; text-align: center; border-radius: 3px;
                       font-size: 10px; font-weight: 700; color: #fff; margin-right: 2px; }}
      .wa-W {{ background: {T['teal']}; }} .wa-D {{ background: {T['grey']}; }} .wa-L {{ background: {T['accent']}; }}
      .wa-prob {{ display: flex; height: 24px; border-radius: 5px; overflow: hidden; font-size: 11px; font-weight: 700; color: #fff; }}
      .wa-prob div {{ display: flex; align-items: center; justify-content: center; }}
      .wa-arch {{ border: 1px solid {T['hair']}; border-radius: 8px; padding: 8px 10px; background: {T['panel2']}; height: 100%; }}
      .wa-arch b {{ font-size: 13px; }} .wa-arch p {{ margin: 3px 0 0; color: {T['muted']}; font-size: 11px; }}
      .wa-arch .n {{ float: right; font-family: Georgia, serif; font-size: 18px; font-weight: 700; color: {T['accent']}; }}
      [data-testid="stMetricValue"] {{ font-family: Georgia, serif; }}
      /* form controls follow the palette even when Streamlit's runtime theme switch is partial */
      [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="input"] input, [data-baseweb="base-input"],
      .stNumberInput input, .stTextInput input, .stNumberInput [data-baseweb="input"] > div {{
        background-color: {T['panel2']} !important; color: {T['ink']} !important; border-color: {T['hair']} !important; }}
      [data-baseweb="select"] div, [data-baseweb="select"] input, [data-baseweb="select"] svg {{ color: {T['ink']} !important; fill: {T['ink']} !important; }}
      [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {{ background-color: {T['panel2']} !important; color: {T['ink']} !important; }}
      [data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{ background-color: {T['chip']} !important; }}
      .stNumberInput button {{ background-color: {T['chip']} !important; color: {T['ink']} !important; }}
      [data-testid="stWidgetLabel"] p, .stRadio label p, .stCheckbox label p {{ color: {T['ink']} !important; }}
      .stRadio [role="radiogroup"] label > div:first-child {{ border-color: {T['muted']} !important; background-color: {T['panel2']} !important; }}
      .stRadio [role="radiogroup"] label[data-checked="true"] > div:first-child,
      .stRadio [role="radiogroup"] input:checked + div {{ background-color: {T['accent']} !important; border-color: {T['accent']} !important; }}
      .stButton button, .stDownloadButton button {{ border-color: {T['hair']} !important; }}
      .stButton button[kind="secondary"], .stDownloadButton button[kind="secondary"] {{ background-color: {T['panel2']} !important; color: {T['ink']} !important; }}
      [data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {T['hair']} !important; }}
      code {{ color: {T['teal']} !important; background: {T['chip']} !important; }}
    </style>""", unsafe_allow_html=True)


def mpl(T: dict):
    plt.rcParams.update({
        "figure.facecolor": T["panel"], "axes.facecolor": T["panel"], "savefig.facecolor": T["panel"],
        "text.color": T["ink"], "axes.labelcolor": T["muted"], "xtick.color": T["muted"], "ytick.color": T["muted"],
        "axes.edgecolor": T["hair"], "grid.color": T["hair"], "font.family": "sans-serif",
        "font.sans-serif": [SANS, "Helvetica", "Arial", "DejaVu Sans"], "font.size": 9, "axes.titleweight": "bold",
        "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42,
    })
