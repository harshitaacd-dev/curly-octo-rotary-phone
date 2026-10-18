"""Figure: where the signal of AI image abuse disappears, from searches to police records (2023 -> 2024).

Usage: python scripts/funnel_figure.py   (writes analysis/funnel/funnel_2023_2024.png, .csv)

Each row is one stage of the reporting chain, national totals for India: the 2024 level as a multiple
of the 2023 level (log scale; 1x = no change). Online stages come from Google Ads search volumes and
the IT Rules grievance reports; recorded stages come from NCRB. Complaints to the national cyber crime
reporting portal are a missing stage: no category breakdown is published.
"""
import os

import matplotlib.pyplot as plt
import pandas as pd

OUT = "analysis/funnel"
ONLINE, RECORDED = "#2a78d6", "#eb6834"  # validated categorical slots 1 and 2 (dataviz palette)
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"


def series():
    pm = pd.read_csv("data/analysis/platform_month_panel.csv")
    pm["year"] = pm.month.str[:4].astype(int)

    def total(platforms, group):
        d = pm[pm.platform.isin(platforms) & (pm.category_group == group) & (pm.suspect_duplicate == 0)]
        return d.groupby("year")["count"].sum()

    nud = pm.groupby("month").ads_national_nudify_searches.first()
    nud = nud.groupby(nud.index.str[:4].astype(int)).sum()
    s = pd.read_csv("data/analysis/state_year_panel.csv").groupby("year").sum(numeric_only=True)
    rows = [
        ("Searches for nudify tools", "Google Ads, India", "online", nud),
        ("Complaints to X: synthetic or manipulated media", "IT Rules reports", "online", total(["X"], "synthetic")),
        ("Complaints to X: sexual content", "IT Rules reports", "online", total(["X"], "sexual")),
        ("Complaints to Facebook, Instagram: own intimate images", "IT Rules reports", "online",
         total(["Facebook", "Instagram"], "sexual")),
        ("Reports to Snapchat: sexual content", "IT Rules reports", "online", total(["Snapchat"], "sexual")),
        ("Complaints to the national cyber crime portal", "no category data published", "missing", None),
        ("Police-recorded cyber crime against women", "NCRB", "recorded", s.cyber_vaw_cases),
        ("   of which obscene or sexual material", "NCRB", "recorded", s.cyber_vaw_obscene_material),
        ("   of which morphing", "NCRB", "recorded", s.cyber_vaw_morphing),
    ]
    out = []
    for label, src, kind, ser in rows:
        a, b = (float(ser.get(2023)), float(ser.get(2024))) if ser is not None else (None, None)
        out.append({"stage": label.strip(), "source": src, "kind": kind, "y2023": a, "y2024": b,
                    "ratio_2024_to_2023": round(b / a, 3) if a else None, "label": label})
    return pd.DataFrame(out)


def draw(df, path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})
    fig, ax = plt.subplots(figsize=(8.6, 5.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ys = list(range(len(df)))[::-1]
    for y, (_, r) in zip(ys, df.iterrows()):
        if r.kind == "missing":
            ax.text(1, y, "no data", ha="center", va="center", color=MUTED, fontsize=8.5, style="italic")
            continue
        color = ONLINE if r.kind == "online" else RECORDED
        ratio = r.ratio_2024_to_2023
        ax.barh(y, ratio - 1 if ratio >= 1 else -(1 - ratio), left=1, height=0.58, color=color, linewidth=0)
        txt = f"{ratio:.2f}×" if ratio < 10 else f"{ratio:.0f}×"
        ax.text(ratio * (1.12 if ratio >= 1 else 0.89), y, txt, va="center",
                ha="left" if ratio >= 1 else "right", color=INK, fontsize=8.8)
    ax.set_xscale("log")
    ax.set_xlim(0.25, 60)
    ax.axvline(1, color=MUTED, linewidth=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r.label}\n({r.source})" for _, r in df.iterrows()], fontsize=8.2, color=INK)
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50])
    ax.set_xticklabels(["0.5×", "1×", "2×", "5×", "10×", "20×", "50×"], color=MUTED)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0, which="both")
    ax.set_xlabel("2024 level as a multiple of 2023 (log scale; 1× = no change)", color=MUTED, fontsize=8.5)
    fig.suptitle("The AI-abuse signal rises online but not in police records", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    fig.text(0.01, 0.905, "India, national totals, 2023 to 2024. Blue: online stages. Orange: police-recorded (NCRB).",
             ha="left", fontsize=8.8, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, facecolor=SURFACE)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = series()
    df.drop(columns="label").to_csv(os.path.join(OUT, "funnel_2023_2024.csv"), index=False)
    draw(df, os.path.join(OUT, "funnel_2023_2024.png"))
    print(df.drop(columns="label").to_string(index=False))


if __name__ == "__main__":
    main()
