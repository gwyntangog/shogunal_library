"""
visualize_momijiyama.py
Charts from data/momijiyama/clean/books_clean.csv. Saves PNGs to figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

CLEAN = Path("momijiyama_data/clean/books_clean.csv")
FIG = Path("figures")
FIG.mkdir(exist_ok=True)

# Japanese-capable fonts that ship with Windows, macOS, or are common installs.
CJK_CANDIDATES = [
    "Yu Gothic", "Meiryo", "MS Gothic", "Yu Mincho",   # Windows
    "Hiragino Sans", "Hiragino Mincho ProN",           # macOS
    "Noto Sans CJK JP", "IPAexGothic",                 # Linux / manual installs
]
installed = {f.name for f in font_manager.fontManager.ttflist}
cjk_fonts = [f for f in CJK_CANDIDATES if f in installed]

if cjk_fonts:
    plt.rcParams["font.family"] = cjk_fonts[:1] + ["DejaVu Sans"]
    print("Using CJK font:", cjk_fonts[0])
else:
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    print("WARNING: no Japanese font found. Japanese text will show as boxes.")

plt.rcParams["axes.unicode_minus"] = False

books = pd.read_csv(CLEAN, encoding="utf-8-sig")
books["edition_origin"] = books["edition_origin"].fillna("unspecified")
books["section"] = books["section"].fillna("unspecified")
N = len(books)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=200)
    plt.close(fig)
    print("saved", FIG / name)


# 1. Bar: edition origin counts (include "unspecified" so the gap is visible)
counts = books["edition_origin"].value_counts()
fig, ax = plt.subplots(figsize=(8, 4.5))
counts.sort_values().plot.barh(ax=ax, color="#8c564b")
ax.set_xlabel("Number of records")
ax.set_ylabel("")
ax.set_title(f"Edition origin, book records (n={N})")
for i, v in enumerate(counts.sort_values()):
    ax.text(v + 0.1, i, str(v), va="center")
save(fig, "01_edition_origin_bar.png")

# 2. Pie: only records with a known origin. Pies are unreadable past ~6 slices.
known = counts.drop("unspecified", errors="ignore")
if len(known) > 6:
    known = pd.concat([known.iloc[:5], pd.Series({"Other": known.iloc[5:].sum()})])
fig, ax = plt.subplots(figsize=(6.5, 6.5))
ax.pie(known.values, labels=known.index, autopct="%1.0f%%", startangle=90, counterclock=False)
ax.set_title(
    f"Share of records with a known edition origin\n"
    f"(n={int(known.sum())} of {N}; {counts.get('unspecified', 0)} unspecified excluded)"
)
ax.axis("equal")
save(fig, "02_edition_origin_pie.png")

# 3. Stacked bar: section (經/史/子/集/國書…) by edition origin
ct = pd.crosstab(books["section"], books["edition_origin"])
fig, ax = plt.subplots(figsize=(9, 5))
ct.plot.bar(stacked=True, ax=ax, colormap="tab10", width=0.7)
ax.set_xlabel("")
ax.set_ylabel("Number of records")
ax.set_title("Catalogue section by edition origin")
ax.legend(title="Edition origin", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
save(fig, "03_section_by_origin_stacked.png")

# 4. Timeline: era year mentioned in the record vs. edition origin
dated = books.dropna(subset=["era_year"]).copy()
if len(dated):
    cats = sorted(dated["edition_origin"].unique())
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, cat in enumerate(cats):
        g = dated[dated["edition_origin"] == cat]
        y = i + rng.uniform(-0.15, 0.15, len(g))  # jitter so points don't overlap
        ax.scatter(g["era_year"], y, s=40, label=cat)
        for xv, yv, t in zip(g["era_year"], y, g["Title_and_Author"].fillna("")):
            ax.annotate(t[:8], (xv, yv), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cats)
    ax.set_xlabel("Year mentioned in the record (era year, converted to Western year)")
    ax.set_title("Dates mentioned in provenance records, by edition origin")
    ax.grid(axis="x", alpha=0.3)
    save(fig, "04_timeline_dot.png")
else:
    print("No era years found; skipping timeline. Check era_year in the QA report.")

# 5. Heatmap: route type by edition origin.
#    explode() repeats index labels, so reset the index before crosstab.
exp = (
    books.assign(route=books["route_types"].fillna("none").str.split("|"))
    .explode("route")
    .reset_index(drop=True)
)
rt = pd.crosstab(exp["route"], exp["edition_origin"])

fig, ax = plt.subplots(figsize=(9, 4.5))
im = ax.imshow(rt.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(rt.shape[1]))
ax.set_xticklabels(rt.columns, rotation=30, ha="right")
ax.set_yticks(range(rt.shape[0]))
ax.set_yticklabels(rt.index)
for i in range(rt.shape[0]):
    for j in range(rt.shape[1]):
        v = rt.values[i, j]
        if v:
            ax.text(j, i, str(v), ha="center", va="center",
                    color="white" if v > rt.values.max() / 2 else "black", fontsize=9)
fig.colorbar(im, ax=ax, label="Records")
ax.set_title("Route type (heuristic) by edition origin")
save(fig, "05_route_by_origin_heatmap.png")
