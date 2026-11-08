"""Download bar for every view: PDF (charts + tables), Excel (one sheet per table), CSV (one table or all as zip), JSON;
plus the whole-league files written by the daily agent."""
from __future__ import annotations

import io
import json
import re
import zipfile
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages

from . import data
from .charts import fig_table
from .style import SERIF


def fname(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def frames(sheets: dict) -> dict[str, pd.DataFrame]:
    return {k: (v if isinstance(v, pd.DataFrame) else pd.DataFrame(v)) for k, v in sheets.items()}


def excel_bytes(sheets: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        head = xw.book.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#14202B"})
        used = set()
        for name, df in frames(sheets).items():
            sheet = re.sub(r"[\[\]:*?/\\]", " ", name)[:31] or "Sheet"
            while sheet in used:
                sheet = sheet[:28] + "_" + str(len(used))
            used.add(sheet)
            df = df.copy()
            for c in df.columns:
                if df[c].map(lambda v: isinstance(v, (dict, list))).any():
                    df[c] = df[c].map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
            df.to_excel(xw, sheet_name=sheet, index=False)
            ws = xw.sheets[sheet]
            for i, c in enumerate(df.columns):
                ws.write(0, i, c, head)
                w = max([len(str(c))] + [len(str(v)) for v in df[c].head(150)]) if len(df) else len(str(c))
                ws.set_column(i, i, min(max(8, w + 2), 40))
            ws.freeze_panes(1, 1)
            if len(df):
                ws.autofilter(0, 0, len(df), max(0, len(df.columns) - 1))
    return buf.getvalue()


def csv_zip(sheets: dict, stem: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k, df in frames(sheets).items():
            if len(df):
                z.writestr(f"{stem}/{fname(k).lower()}.csv", df.to_csv(index=False).encode("utf-8-sig"))
    return buf.getvalue()


def pdf_bytes(title: str, subtitle: str, figs: list, sheets: dict, T: dict) -> bytes:
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        cover = plt.figure(figsize=(11.69, 8.27))
        cover.text(0.05, 0.86, "WALTZING ANALYTICS · XDANGER", color=T["accent"], fontsize=11, fontweight="bold")
        cover.text(0.05, 0.76, title, fontsize=30, fontweight="bold", family=SERIF, color=T["ink"])
        cover.text(0.05, 0.70, subtitle, fontsize=12, color=T["muted2"])
        cover.text(0.05, 0.08, "Data: IMPECT, Opta, StatsBomb, SkillCorner, Transfermarkt · Models: Waltzing Analytics",
                   fontsize=9, color=T["muted"])
        pdf.savefig(cover)
        plt.close(cover)
        for f in figs:
            w, h = f.get_size_inches()
            f.set_size_inches(max(w, 7), max(h, 5))
            pdf.savefig(f)
        for name, df in frames(sheets).items():
            if not len(df):
                continue
            for start in range(0, min(len(df), 112), 28):
                page = fig_table(df.iloc[start:start + 28], T, name, f"{title} · rows {start + 1}-{min(len(df), start + 28)} of {len(df)}")
                pdf.savefig(page)
                plt.close(page)
    return buf.getvalue()


def bar(key: str, name: str, sheets: dict, payload, figs_fn: Callable[[], list] | None, T: dict, league: dict):
    """The export bar. figs_fn builds the figures for the PDF only when the PDF is asked for."""
    stem = fname(f"WA_{name}")
    with st.container(border=True):
        c = st.columns([1.15, 1, 1.5, 1, 0.15, 1.4, 1.2, 1])
        with c[0]:
            k = f"pdf_{key}_{stem}_{T['base']}"
            if st.session_state.get(k) is None:
                if st.button("Make PDF", key=f"mk_{k}", type="primary", width="stretch",
                             help="Builds a PDF of this view (charts and tables) in the active theme"):
                    with st.spinner("Building PDF…"):
                        figs = figs_fn() if figs_fn else []
                        st.session_state[k] = pdf_bytes(name, f"{league['name']} 2026-27 · {key}", figs, sheets, T)
                        for f in figs:
                            plt.close(f)
                    st.rerun()
            else:
                st.download_button("Download PDF", st.session_state[k], f"{stem}.pdf", "application/pdf",
                                   type="primary", width="stretch", key=f"dl_{k}")
        with c[1]:
            st.download_button("Excel", excel_bytes(sheets), f"{stem}.xlsx", width="stretch",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"x_{key}")
        with c[2]:
            fr = {k_: v for k_, v in frames(sheets).items() if len(v)}
            opts = ["All tables (zip)"] + list(fr)
            pick = st.selectbox("CSV", opts, label_visibility="collapsed", key=f"csvpick_{key}")
        with c[3]:
            if pick == "All tables (zip)":
                st.download_button("CSV", csv_zip(fr, stem), f"{stem}_csv.zip", "application/zip",
                                   width="stretch", key=f"c_{key}")
            else:
                st.download_button("CSV", fr[pick].to_csv(index=False).encode("utf-8-sig"), f"{stem}_{fname(pick)}.csv",
                                   "text/csv", width="stretch", key=f"c_{key}")
        with c[4]:
            st.write("")
        with c[5]:
            xf = data.league_file(league["key"], "xlsx")
            if xf:
                st.download_button("League Excel", xf[1], xf[0], width="stretch", key=f"lx_{key}",
                                   help="Every table of the league, 20 sheets")
        with c[6]:
            cf = data.league_file(league["key"], "csv")
            if cf:
                st.download_button("League CSV", cf[1], cf[0], "application/zip", width="stretch", key=f"lc_{key}")
        with c[7]:
            st.download_button("JSON", json.dumps(payload, ensure_ascii=False, indent=1, default=str), f"{stem}.json",
                               "application/json", width="stretch", key=f"j_{key}")
