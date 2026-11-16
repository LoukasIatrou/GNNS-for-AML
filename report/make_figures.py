"""Build every report figure from the committed result tables.

Run from the repository root:  python report/make_figures.py
Inputs:  tests/elliptic_split.csv, results/final_comparison/*.csv, results/explainability/*.csv
Outputs: report/figures/*.png (used by report/build_report.py) and *.pdf (vector copies)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES, FIG = ROOT / "results", ROOT / "report" / "figures"
FIG.mkdir(exist_ok=True)

# Fixed model order, colour and marker (palette validated for colour-vision deficiency).
MODELS = {
    "RandomForest_Role2": ("Random Forest (Role 2)", "#2a78d6", "o"),
    "RandomForest_Role3": ("Random Forest (Role 3)", "#eb6834", "s"),
    "GCN": ("GCN", "#1baf7a", "^"),
    "GraphSAGE": ("GraphSAGE", "#eda100", "D"),
    "GAT": ("GAT", "#e87ba4", "v"),
    "MLP": ("MLP (no graph)", "#008300", "P"),
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SHIFT, TEST_START = 43, 35
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Calibri", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "lines.linewidth": 1.6, "lines.markersize": 4.5, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf"); fig.savefig(FIG / f"{name}.png", dpi=220); plt.close(fig)


def shift_line(ax, label=True):
    ax.axvline(SHIFT - 0.5, color=MUTED, ls=":", lw=1)
    if label:
        ax.text(SHIFT - 0.3, ax.get_ylim()[1] * 0.97, "dark-market\nshutdown", va="top", fontsize=7, color=MUTED)


# 1. Data: illicit transactions over time (Role 1 story)
split = pd.read_csv(ROOT / "tests" / "elliptic_split.csv", dtype={"class": str})
lab = split[split["class"] != "unknown"]
per_t = lab.groupby("time_step")["class"].agg(illicit=lambda c: (c == "illicit").sum(), n="size")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4))
axes[0].bar(per_t.index, per_t["illicit"], color="#2a78d6", width=0.8)
axes[0].set(xlabel="time step", ylabel="illicit transactions")
axes[1].plot(per_t.index, per_t["illicit"] / per_t["n"] * 100, color="#2a78d6", marker="o")
axes[1].set(xlabel="time step", ylabel="illicit share of labelled (%)")
for ax in axes:
    ax.axvline(TEST_START - 0.5, color=INK, ls="--", lw=1)
    ax.text(TEST_START - 0.2, ax.get_ylim()[1] * 0.97, "test", va="top", fontsize=7, color=INK)
    shift_line(ax, label=False)
    ax.text(SHIFT, ax.get_ylim()[1] * 0.80, "shutdown", fontsize=7, color=MUTED)
save(fig, "fig1_illicit_over_time")

# 2. Model comparison: AP and F1, mean ± std over 5 seeds
summary = pd.read_csv(RES / "final_comparison" / "summary.csv").set_index("model").loc[list(MODELS)]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.5), sharey=True)
y = np.arange(len(MODELS))[::-1]
for ax, metric, title in zip(axes, ["average_precision", "f1_illicit"], ["Average precision (AP)", "Illicit F1"]):
    for yi, (m, (name, col, _)) in zip(y, MODELS.items()):
        mean, std = summary.loc[m, f"{metric}_mean"], summary.loc[m, f"{metric}_std"]
        ax.barh(yi, mean, xerr=std, color=col, height=0.6, error_kw=dict(ecolor=INK, lw=0.8, capsize=2))
        ax.text(mean + std + 0.015, yi, f"{mean:.3f}", va="center", fontsize=7.5, color=INK)
    ax.set(xlim=(0, 1), title=title)
    ax.grid(axis="y", visible=False)
axes[0].set_yticks(y, [v[0] for v in MODELS.values()])
save(fig, "fig2_model_comparison")

# 3. F1 per test time step (mean over seeds)
steps = pd.read_csv(RES / "final_comparison" / "per_time_step_runs.csv")
f1 = steps.groupby(["model", "time_step"])["f1_illicit"].mean().unstack(0)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
for m, (name, col, mk) in MODELS.items():
    ax.plot(f1.index, f1[m], color=col, marker=mk, label=name)
ax.set(xlabel="test time step", ylabel="illicit F1 (mean of 5 seeds)", ylim=(0, 1.02), xticks=f1.index)
shift_line(ax)
ax.legend(ncol=3, fontsize=7.5, loc="upper right", bbox_to_anchor=(1, 1.22))
save(fig, "fig3_f1_per_time_step")

# 4. Precision-recall curves (seed 0)
pr = pd.read_csv(RES / "final_comparison" / "pr_curves_seed0.csv")
fig, ax = plt.subplots(figsize=(5.4, 3.0))
for m, (name, col, mk) in MODELS.items():
    d = pr[pr["model"] == m]
    ax.plot(d["recall"], d["precision"], color=col, label=name, marker=mk, markevery=10)
ax.axhline(1083 / 16670, color=MUTED, ls=":", lw=1)
ax.text(0.02, 1083 / 16670 + 0.02, "random (6.5%)", fontsize=7, color=MUTED)
ax.set(xlabel="recall", ylabel="precision", xlim=(0, 1), ylim=(0, 1.02))
ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.02, 1))
save(fig, "fig4_pr_curves")

# 5. SHAP importance, Role 2 Random Forest (local vs aggregated features)
imp = pd.read_csv(RES / "explainability" / "rf_shap_importance.csv").head(15)[::-1]
local = imp["feature"].str.split("_").str[1].astype(int) <= 93
fig, ax = plt.subplots(figsize=(3.6, 3.2))
ax.barh(imp["feature"], imp["mean_abs_shap"], color=np.where(local, "#2a78d6", "#eb6834"), height=0.65)
from matplotlib.patches import Patch
ax.set(xlabel="mean |SHAP| (illicit probability)")
ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(color="#2a78d6", label="local feature (1–93)"),
                   Patch(color="#eb6834", label="aggregated feature (94–165)")], fontsize=7, loc="lower right")
save(fig, "fig5_shap_importance")

# 6. SHAP drift: contribution of the top features for illicit transactions before/after the shutdown
drift = pd.read_csv(RES / "explainability" / "rf_shap_drift.csv").set_index("quantity")
shap_rows = drift[drift.index.str.startswith("SHAP ")]
feats = shap_rows.index.str.replace("SHAP ", "")
x = np.arange(len(feats))
fig, ax = plt.subplots(figsize=(3.6, 2.6))
ax.bar(x - 0.2, shap_rows.iloc[:, 0], 0.38, color="#2a78d6", label="illicit, steps 35–42")
ax.bar(x + 0.2, shap_rows.iloc[:, 1], 0.38, color="#eb6834", label="illicit, steps 43–49")
ax.axhline(0, color=INK, lw=0.8)
ax.set_xticks(x, feats, rotation=45, ha="right")
ax.set(ylabel="mean SHAP (→ illicit)")
ax.legend(fontsize=7, loc="upper right")
save(fig, "fig6_shap_drift")

# 7. Graph ablation: test AP with and without edges, per seed
abl = pd.read_csv(RES / "explainability" / "graph_ablation.csv")
fig, ax = plt.subplots(figsize=(3.6, 2.6))
for i, (m, key) in enumerate([("GCN", "GCN"), ("SAGE", "GraphSAGE")]):
    d = abl[abl["model"] == m]
    _, col, mk = MODELS[key]
    for _, r in d.iterrows():
        ax.plot([i * 2.5, i * 2.5 + 1], [r["ap_with_edges"], r["ap_without_edges"]], color=col, marker=mk, lw=1, alpha=0.8)
    ax.plot([i * 2.5, i * 2.5 + 1], [d["ap_with_edges"].mean(), d["ap_without_edges"].mean()], color=INK, lw=2.2, marker="_", ms=12)
ax.set_xticks([0, 1, 2.5, 3.5], ["GCN\nwith edges", "GCN\nno edges", "GraphSAGE\nwith edges", "GraphSAGE\nno edges"], fontsize=7.5)
ax.set(ylabel="test AP", xlim=(-0.5, 4))
ax.grid(axis="x", visible=False)
save(fig, "fig7_graph_ablation")

print("figures:", sorted(p.name for p in FIG.glob("*.png")))
