"""Draws Figure 2 of the report from the event-study estimates saved by analysis.py.

Run analysis.py first. It writes output/event_H2b.csv and output/event_H3a.csv.
This script reads those two files and saves output/figure2.png.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

O = "output"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "TeX Gyre Termes", "DejaVu Serif"], "font.size": 11})
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.9))
panels = [("event_H2b.csv", "(a) Tesla’s market share × Home charging"),
          ("event_H3a.csv", "(b) Total registrations × Commercial alternatives")]
for ax, (f, title) in zip(axs, panels):
    d = pd.read_csv(f"{O}/{f}")[["q", "Estimate", "2.5%", "97.5%"]]
    # 2023Q4 is the reference quarter, so its estimate is zero by construction
    d = pd.concat([d, pd.DataFrame([{"q": "2023Q4", "Estimate": 0, "2.5%": 0, "97.5%": 0}])]).sort_values("q").reset_index(drop=True)
    x = range(len(d))
    first = list(d.q).index("2024Q1") - 0.5
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(first, color="black", lw=0.9, ls=(0, (4, 3)))
    ax.vlines(x, d["2.5%"], d["97.5%"], color="0.45", lw=1.1)
    ax.plot(x, d.Estimate, "o", color="black", ms=4.5)
    ax.plot([list(d.q).index("2023Q4")], [0], "o", mfc="white", mec="black", ms=4.5)
    ax.set_xticks(list(x)); ax.set_xticklabels([q if q.endswith("Q1") else "" for q in d.q], fontsize=10)
    ax.set_title(title, fontsize=11.5, loc="left"); ax.set_xlabel("Quarter of sale")
    ax.text(first + 0.25, ax.get_ylim()[1] * 0.88, "First access\n(March 2024)", fontsize=9.5, va="top")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axs[0].set_ylabel("Difference from 2023 Q4 (log points)")
fig.tight_layout(); fig.savefig(f"{O}/figure2.png", dpi=300, bbox_inches="tight")
print("saved output/figure2.png")
