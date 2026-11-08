"""Every chart as a matplotlib figure in the active palette, so the same figure is shown in the app and written to PDF.

Pitch frame: IMPECT coordinates, x towards the attacked goal (0 to 52.5), y positive = the attacker's left.
Half pitches are drawn vertically with the goal at the top.
"""
from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Rectangle, Wedge

from .style import SERIF

CAT_COLORS = {"Shooting": "accent", "Creating": "gold", "Possession": "teal", "Defending": "blue",
              "Physical": "muted2", "Overall": "ink"}


def _title(fig, title, sub, T):
    if title:
        fig.text(0.02, 0.975, title, ha="left", va="top", fontsize=13, fontweight="bold", family=SERIF, color=T["ink"])
    if sub:
        fig.text(0.02, 0.93 if title else 0.975, sub, ha="left", va="top", fontsize=8, color=T["muted"])


def half_pitch(ax, T):
    ax.set_facecolor(T["pitch"])
    lc = dict(color=T["line"], lw=1.1, fill=False)
    X = lambda y: -y  # noqa: E731
    ax.add_patch(Rectangle((X(34), 0), 68, 52.5, **lc))
    ax.add_patch(Rectangle((X(20.16), 52.5 - 16.5), 40.32, 16.5, **lc))
    ax.add_patch(Rectangle((X(9.16), 52.5 - 5.5), 18.32, 5.5, **lc))
    ax.plot([-3.66, 3.66], [52.9, 52.9], color=T["ink"], lw=3, solid_capstyle="butt")
    ax.add_patch(Circle((0, 52.5 - 11), 0.35, color=T["line"]))
    ax.add_patch(Arc((0, 52.5 - 11), 18.3, 18.3, theta1=233, theta2=307, color=T["line"], lw=1.1))
    ax.add_patch(Arc((0, 0), 18.3, 18.3, theta1=0, theta2=180, color=T["line"], lw=1.1))
    ax.set_xlim(-35, 35)
    ax.set_ylim(-1, 54)
    ax.set_aspect("equal")
    ax.axis("off")


def fig_shots(m, side, T, title=None):
    col = T["accent"] if side == 0 else T["blue"]
    fig, ax = plt.subplots(figsize=(6, 4.9))
    half_pitch(ax, T)
    for s in m["post"]["shots"]:
        if s[0] != side:
            continue
        xg = s[4] or 0.01
        size = max(30, math.sqrt(xg) * 900)
        kw = dict(s=size, linewidths=1.6, edgecolors=col, facecolors=col if s[5] else "none", zorder=3,
                  marker="s" if s[8] else "o", alpha=0.95)
        ax.scatter(-s[3], s[2], **kw)
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.88)
    _title(fig, title or f"Shots: {m['away'] if side else m['home']}", "Size = xG · filled = goal · square = set piece", T)
    return fig


def fig_race(m, T):
    P = m["post"]
    end = max([95] + [s[1] or 0 for s in P["shots"]])
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for side, col, team in ((0, T["accent"], m["home"]), (1, T["blue"], m["away"])):
        xs, ys, tot = [0], [0], 0.0
        goals = []
        for s in P["shots"]:
            if s[0] != side:
                continue
            xs += [s[1], s[1]]
            ys += [tot, tot + (s[4] or 0)]
            tot += s[4] or 0
            if s[5]:
                goals.append((s[1], tot, s[6]))
        xs.append(end)
        ys.append(tot)
        ax.plot(xs, ys, color=col, lw=2.2, label=f"{team} {tot:.2f}")
        for gx, gy, nm in goals:
            ax.scatter(gx, gy, s=55, color=col, edgecolors=T["panel"], zorder=4)
    for t in (45, 90):
        ax.axvline(t, color=T["hair"], lw=0.8)
    ax.set_xlim(0, end)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xticklabels([f"{t}'" for t in [0, 15, 30, 45, 60, 75, 90]])
    ax.set_ylabel("cumulative xG")
    ax.legend(frameon=False, loc="upper left", fontsize=8, labelcolor=T["ink"])
    fig.subplots_adjust(0.09, 0.12, 0.98, 0.84)
    _title(fig, "xG race", "Cumulative xG; dots are goals", T)
    return fig


def fig_momentum(m, T):
    M = np.array(m["post"]["momentum"], dtype=float)
    fig, ax = plt.subplots(figsize=(7, 2.8))
    x = np.arange(len(M)) * 5 + 2.5
    ax.bar(x, M[:, 0], width=4.2, color=T["accent"])
    ax.bar(x, -M[:, 1], width=4.2, color=T["blue"])
    ax.axhline(0, color=T["hair"], lw=0.8)
    ax.axvline(45, color=T["muted"], lw=0.8, ls=":")
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xticklabels([f"{t}'" for t in [0, 15, 30, 45, 60, 75, 90]])
    mx = max(0.05, np.abs(M).max()) * 1.1
    ax.set_ylim(-mx, mx)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fig.subplots_adjust(0.03, 0.14, 0.98, 0.80)
    _title(fig, "xDanger momentum", f"Positive xDanger added per 5 minutes: {m['home']} up, {m['away']} down", T)
    return fig


MATCH_STATS = [("xG", "xg", 2), ("Non-pen xG", "npxg", 2), ("xGOT", "xgot", 2), ("Shots", "shots", 0),
               ("On target", "on_target", 0), ("xDanger", "xd", 2), ("xDanger won", "xd_won", 2),
               ("xDanger denied", "xd_denied", 2), ("xShot added", "xshot", 1), ("Possession", "poss", "%"),
               ("Field tilt", "field_tilt", "%"), ("Box entries", "box_entries", 0), ("Golden-zone touches", "golden", 0),
               ("High regains", "high_regains", 0), ("Corners", "corners", 0), ("Set-piece xG", "sp_xg", 2),
               ("Passes", "passes", 0)]


def fig_match_numbers(m, T):
    a, b = m["post"]["stats"]
    fig, ax = plt.subplots(figsize=(6.5, 6.2))
    n = len(MATCH_STATS)
    for i, (lab, k, d) in enumerate(MATCH_STATS):
        y = n - i
        va, vb = a.get(k) or 0, b.get(k) or 0
        mx = max(va, vb, 1e-9)
        ax.barh(y, -va / mx, height=0.5, color=T["accent"], left=-0.28)
        ax.barh(y, vb / mx, height=0.5, color=T["blue"], left=0.28)
        ax.barh(y, -1, height=0.5, color=T["chip"], left=-0.28, zorder=0)
        ax.barh(y, 1, height=0.5, color=T["chip"], left=0.28, zorder=0)
        fmt = (lambda v: f"{v * 100:.0f}%") if d == "%" else (lambda v, d=d: f"{v:.{d}f}")
        ax.text(-1.33, y, fmt(va), ha="right", va="center", fontweight="bold", fontsize=9)
        ax.text(1.33, y, fmt(vb), ha="left", va="center", fontweight="bold", fontsize=9)
        ax.text(0, y, lab, ha="center", va="center", fontsize=8, color=T["muted2"])
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(0.3, n + 0.7)
    ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.90)
    _title(fig, "Match numbers", f"{m['home']} (left) v {m['away']} (right) · WA xDanger models on IMPECT", T)
    return fig


def fig_corner_map(points, T, title, sub="End points folded so every corner comes from the left; coral = goal, size = xG"):
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    half_pitch(ax, T)
    ax.set_ylim(25, 54)
    for x, y, goal, xg in points or []:
        ax.scatter(-y, x, s=max(14, math.sqrt(xg or 0) * 260), color=T["accent"] if goal else T["blue"],
                   alpha=0.95 if goal else 0.45, linewidths=0, zorder=3)
    ax.scatter(-34, 52.5, s=50, color=T["ink"], zorder=4)
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.84)
    _title(fig, title, sub, T)
    return fig


def fig_goal_mouth(pens, T, title="Penalty placement"):
    fig, ax = plt.subplots(figsize=(7, 3.3))
    ax.set_facecolor(T["pitch"])
    ax.plot([-3.66, -3.66, 3.66, 3.66], [0, 2.44, 2.44, 0], color=T["ink"], lw=4)
    ax.axhline(0, color=T["line"], lw=1)
    for xx in (-1.22, 1.22):
        ax.plot([xx, xx], [0, 2.44], color=T["hair"], ls=":", lw=1)
    ax.plot([-3.66, 3.66], [1.22, 1.22], color=T["hair"], ls=":", lw=1)
    for p in pens:
        if p.get("ty") is None or p.get("tz") is None:
            continue
        ax.scatter(-p["ty"], max(0.08, p["tz"]), s=90, color=T["accent"] if p["goal"] else T["blue"], alpha=0.85,
                   edgecolors=T["panel"], zorder=3)
    ax.set_xlim(-5, 5)
    ax.set_ylim(-0.3, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.84)
    _title(fig, title, "Shooter's view · coral = scored, blue = saved or missed", T)
    return fig


def fig_xd_scatter(table, T, league):
    fig, ax = plt.subplots(figsize=(7, 5.6))
    xs = [t["xd_f"] for t in table]
    ys = [t["xd_a"] for t in table]
    ax.axvline(np.mean(xs), color=T["hair"], ls="--", lw=0.8)
    ax.axhline(np.mean(ys), color=T["hair"], ls="--", lw=0.8)
    for t in table:
        ax.scatter(t["xd_f"], t["xd_a"], s=45, color=T["accent"] if t["xd_diff"] >= 0 else T["blue"],
                   edgecolors=T["panel"], zorder=3)
        ax.annotate(short(t["team"]), (t["xd_f"], t["xd_a"]), xytext=(5, 2), textcoords="offset points", fontsize=7,
                    color=T["ink"])
    ax.invert_yaxis()
    ax.set_xlabel("xDanger for per match")
    ax.set_ylabel("xDanger against per match (fewer at top)")
    fig.subplots_adjust(0.11, 0.1, 0.97, 0.86)
    _title(fig, "xDanger for vs against", f"{league} · top right = dangerous and hard to hurt", T)
    return fig


def short(s):
    import re
    return re.sub(r"^(FC|SC|SV|VfL|VfB|TSG|1\. FC|1\. FSV|SpVgg|KV|KAA|RSC|Royal|FK|SK) ", "", str(s or ""))


def fig_pizza(rows, T, title, sub):
    R = [r for r in rows if r["percentile"] is not None]
    fig = plt.figure(figsize=(7.2, 7.4))
    ax = fig.add_axes([0.08, 0.04, 0.84, 0.80])
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect("equal")
    ax.axis("off")
    n = len(R)
    if not n:
        ax.text(0, 0, "Not enough data", ha="center", color=T["muted"])
        return fig
    r0, R1 = 0.15, 1.0
    step = 360 / n
    for q in (25, 50, 75, 100):
        ax.add_patch(Circle((0, 0), r0 + (R1 - r0) * q / 100, fill=False, color=T["hair"], lw=0.8,
                            ls="-" if q == 100 else ":"))
    for i, r in enumerate(R):
        a1 = 90 - i * step - 1
        a0 = a1 - step + 2
        col = T[CAT_COLORS[r["category"]]]
        rr = r0 + (R1 - r0) * max(2, r["percentile"]) / 100
        ax.add_patch(Wedge((0, 0), R1, a0, a1, width=R1 - r0, color=T["chip"], alpha=0.55, lw=0))
        ax.add_patch(Wedge((0, 0), rr, a0, a1, width=rr - r0, color=col, lw=0.8, ec=T["panel"]))
        am = math.radians((a0 + a1) / 2)
        ax.add_patch(Circle((rr * math.cos(am), rr * math.sin(am)), 0.065, color=T["panel2"], ec=col, lw=1.2, zorder=4))
        ax.text(rr * math.cos(am), rr * math.sin(am), str(r["percentile"]), ha="center", va="center", fontsize=7,
                fontweight="bold", zorder=5, color=T["ink"])
        lx, ly = 1.16 * math.cos(am), 1.16 * math.sin(am)
        ha = "center" if abs(math.cos(am)) < 0.25 else ("left" if math.cos(am) > 0 else "right")
        v = r["value"]
        vs = f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}" if abs(v) >= 10 else f"{v:.2f}"
        ax.text(lx, ly + 0.03, r["metric"], ha=ha, va="center", fontsize=7.5, fontweight="bold")
        ax.text(lx, ly - 0.06, vs, ha=ha, va="center", fontsize=7, color=T["muted"])
    ax.add_patch(Circle((0, 0), r0, color=T["panel"], zorder=2))
    cats = list(dict.fromkeys(r["category"] for r in R))
    for j, c in enumerate(cats):
        fig.patches.append(Rectangle((0.03 + j * 0.155, 0.885), 0.014, 0.014, transform=fig.transFigure,
                                     color=T[CAT_COLORS[c]], figure=fig))
        fig.text(0.05 + j * 0.155, 0.892, c, fontsize=7.5, va="center", color=T["muted2"])
    _title(fig, title, sub, T)
    return fig


def fig_radar(axes, series, T, title, sub, avg_label="average"):
    """Deviation radar on plain axes (straight edges between spokes). z clipped to +-2.5; dashed ring = average."""
    n = len(axes)
    fig = plt.figure(figsize=(7.2, 7.4))
    ax = fig.add_axes([0.06, 0.07, 0.88, 0.76])
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.38, 1.38)
    ax.set_aspect("equal")
    ax.axis("off")
    if n < 3:
        ax.text(0, 0, "Not enough data", ha="center", color=T["muted"])
        return fig
    ang = [math.pi / 2 - 2 * math.pi * i / n for i in range(n)]
    rad = lambda z: 0.08 + 0.92 * (max(-2.5, min(2.5, -2.5 if z is None else z)) + 2.5) / 5  # noqa: E731
    pt = lambda i, z: (rad(z) * math.cos(ang[i]), rad(z) * math.sin(ang[i]))  # noqa: E731
    for z in (-2, -1, 0, 1, 2):
        ring = [pt(i, z) for i in range(n)] + [pt(0, z)]
        xs, ys = zip(*ring)
        if z == 0:
            ax.fill(xs, ys, color=T["chip"], alpha=0.35, lw=0)
        ax.plot(xs, ys, color=T["muted2"] if z == 0 else T["hair"], lw=1.5 if z == 0 else 0.8, ls="--" if z == 0 else "-")
        x0, y0 = pt(0, z)
        ax.text(x0 + 0.02, y0 + 0.015, avg_label if z == 0 else f"{z:+d} sd", fontsize=6.5, color=T["muted"])
    for i, a in enumerate(axes):
        x1, y1 = pt(i, 2.5)
        ax.plot([0, x1], [0, y1], color=T["hair"], lw=0.6)
        c = math.cos(ang[i])
        ha = "center" if abs(c) < 0.25 else ("left" if c > 0 else "right")
        ax.text(1.1 * math.cos(ang[i]), 1.1 * math.sin(ang[i]), a, ha=ha, va="center", fontsize=7.5, fontweight="bold")
    for se in series:
        pts = [pt(i, z) for i, z in enumerate(se["z"])]
        xs, ys = zip(*(pts + pts[:1]))
        ax.fill(xs, ys, color=se["color"], alpha=0.22, lw=0)
        ax.plot(xs, ys, color=se["color"], lw=2)
        ok = [p_ for p_, z in zip(pts, se["z"]) if z is not None]
        if ok:
            ax.scatter(*zip(*ok), s=18, color=se["color"], zorder=4, edgecolors=T["panel"], linewidths=0.6)
    for j, se in enumerate(series):
        fig.patches.append(Rectangle((0.05 + j * 0.42, 0.03), 0.018, 0.018, transform=fig.transFigure, color=se["color"],
                                     figure=fig))
        fig.text(0.075 + j * 0.42, 0.039, se["name"], fontsize=8.5, va="center")
    _title(fig, title, sub, T)
    return fig


def fig_table(df, T, title, sub="", max_rows=28):
    """A table as a figure page (for PDFs)."""
    d = df.head(max_rows).copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: "" if v != v else (f"{v:.3f}" if abs(v) < 10 else f"{v:.1f}"))
    d = d.astype(str).replace({"None": "", "nan": ""})
    fig = plt.figure(figsize=(11.69, 8.27))
    _title(fig, title, sub, T)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.86])
    ax.axis("off")
    if d.empty:
        return fig
    tb = ax.table(cellText=d.values, colLabels=[str(c) for c in d.columns], loc="upper center", cellLoc="left")
    tb.auto_set_font_size(False)
    tb.set_fontsize(7 if len(d.columns) > 9 else 8)
    tb.scale(1, 1.25)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor(T["hair"])
        cell.set_facecolor(T["panel2"] if r == 0 else T["panel"])
        cell.get_text().set_color(T["muted"] if r == 0 else T["ink"])
        if r == 0:
            cell.get_text().set_fontweight("bold")
    return fig
