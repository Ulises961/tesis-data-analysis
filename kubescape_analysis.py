#!/usr/bin/env python3
"""
Kubescape security analysis: vulnerability ratios, paired comparisons, and visualizations.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from scipy.stats import mannwhitneyu, wilcoxon
from utils import safe_get, rank_biserial_u


def rank_biserial_from_wilcoxon(deltas):
    """Approximate rank-biserial effect size from Wilcoxon deltas."""
    try:
        pos = (deltas > 0).sum()
        neg = (deltas < 0).sum()
        n_pairs = pos + neg
        if n_pairs == 0:
            return 0.0
        return (pos - neg) / n_pairs
    except Exception:
        return np.nan


def analyze_kubescape(results, fig_dir):
    """
    Compare Kubescape misconfiguration levels across all stages.
    Includes Mann-Whitney U tests and summary statistics.
    """
    print("\n" + "="*80)
    print("KUBESCAPE MISCONFIGURATION ANALYSIS")
    print("="*80)

    records = []
    for stage, apps in results.items():
        for app, metrics in apps.items():
            ks = safe_get(metrics, "kubescape", default={})
            total = safe_get(ks, "total_controls", default=0)
            if not total or total == 0:
                continue
            critical = safe_get(ks, "critical", default=0)
            high = safe_get(ks, "high", default=0)
            medium = safe_get(ks, "medium", default=0)
            low = safe_get(ks, "low", default=0)
            failed = critical + high + medium + low # type: ignore
            fail_ratio = failed / total # type: ignore
            fail_pct = fail_ratio * 100
            records.append({
                "stage": stage,
                "app": app,
                "failed": failed,
                "total": total,
                "fail_ratio": fail_ratio,
                "fail_pct": fail_pct,
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            })

    if not records:
        print("No Kubescape data found.")
        return pd.DataFrame()

    dfk = pd.DataFrame(records)
    print(f"Loaded {len(dfk)} Kubescape records across {dfk['stage'].nunique()} stages.")

    summary = dfk.groupby("stage")["fail_ratio"].agg(["mean", "median", "std", "count"]).sort_index()
    print("\n--- Kubescape vulnerability ratio summary ---")
    print(summary.round(4).to_string())

    stage_labels = {
        "without_ir": "Without IR",
        "with_ir": "With IR",
        "with_ir_corrected": "With IR\nCorrected",
        "with_overrides": "IR With\nOverrides",
        "with_overrides_corrected": "IR With Overrides\nCorrected",
    }
    
    stage_order = ["without_ir", "with_ir", "with_ir_corrected", "with_overrides", "with_overrides_corrected"]
    dfk["stage"] = pd.Categorical(dfk["stage"], categories=stage_order, ordered=True)
    dfk["stage_label"] = dfk["stage"].map(stage_labels)

    # Mann-Whitney U tests
    print("\n--- Mann-Whitney U tests (unpaired stage comparisons) ---")
    test_pairs = [
        ("without_ir", "with_ir"),
        ("without_ir", "with_overrides"),
        ("with_ir", "with_ir_corrected"),
        ("with_overrides", "with_overrides_corrected"),
        ("with_ir", "with_overrides"),
        ("with_ir_corrected", "with_overrides_corrected"),
    ]
    
    mwu_results = []
    for s1, s2 in test_pairs:
        d1 = dfk[dfk["stage"] == s1]["fail_ratio"]
        d2 = dfk[dfk["stage"] == s2]["fail_ratio"]
        
        if len(d1) < 2 or len(d2) < 2:
            print(f"{s1} vs {s2}: insufficient data")
            continue
        
        try:
            u_stat, p_val = mannwhitneyu(d1, d2, alternative="two-sided")
            r_rb = rank_biserial_u(u_stat, len(d1), len(d2))
            median_diff = d2.median() - d1.median()
            
            print(f"{s1:25s} vs {s2:25s}: n1={len(d1):2d}, n2={len(d2):2d}, "
                  f"U={u_stat:6.1f}, p={p_val:.4f}, r={r_rb:6.3f}, Δmedian={median_diff:6.4f}")
            
            mwu_results.append({
                "stage_1": s1,
                "stage_2": s2,
                "n1": len(d1),
                "n2": len(d2),
                "U": u_stat,
                "p_value": p_val,
                "rank_biserial": r_rb,
                "median_diff_pct": median_diff,
                "significant": "Yes" if p_val < 0.05 else "No"
            })
        except Exception as e:
            print(f"{s1} vs {s2}: Mann-Whitney failed ({e})")
    

    # Bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(data=dfk, x="stage_label", y="fail_ratio", errorbar="sd", palette="magma", 
                order=[stage_labels[s] for s in stage_order if s in dfk["stage"].values])
    plt.ylim(0, 1.0)
    plt.ylabel("Kubescape Misconfiguration Ratio", fontsize=11, weight="bold")
    plt.xlabel("Stage", fontsize=11, weight="bold")
    plt.title("Average Kubescape Misconfiguration Ratio by Stage", fontsize=12, weight="bold")
    plt.xticks(rotation=0, ha="center", fontsize=9)
    plt.tight_layout()
    outpath = os.path.join(fig_dir, "kubescape_misconfiguration_ratio_by_stage.png")
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"✓ Saved {outpath}")

    # Boxplot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.stripplot(data=dfk, x="stage_label", y="fail_ratio", 
                  order=[stage_labels[s] for s in stage_order if s in dfk["stage"].values],
                  palette="pastel", alpha=0.5, size=4, jitter=0.25, ax=ax)
    sns.boxplot(data=dfk, x="stage_label", y="fail_ratio", 
                order=[stage_labels[s] for s in stage_order if s in dfk["stage"].values],
                hue="stage_label", palette="pastel", showfliers=False, ax=ax,
                boxprops=dict(alpha=0.7), whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5), medianprops=dict(linewidth=2, color='red'),
                legend=False)
    
    ymin = dfk["fail_ratio"].min()
    ymax = dfk["fail_ratio"].max()
    yrange = ymax - ymin
    padding = yrange * 0.15
    ax.set_ylim(max(0, ymin - padding), min(1.0, ymax + padding))
    
    ax.set_ylabel("Failed Controls / Total Controls", fontsize=11, weight="bold")
    ax.set_xlabel("Stage", fontsize=11, weight="bold")
    ax.set_title("Distribution of Kubescape Misconfiguration Ratios (Zoomed)", 
                fontsize=12, weight="bold")
    ax.tick_params(axis='x', rotation=0, labelsize=9)
    plt.tight_layout()
    outpath_box = os.path.join(fig_dir, "kubescape_misconfiguration_ratio_distribution.png")
    plt.savefig(outpath_box, dpi=300)
    plt.close()
    print(f"✓ Saved {outpath_box}")

    print("\n✓ Kubescape analysis complete.\n")
    return dfk


def analyze_kubescape_paired(results, fig_dir, stage_a="with_ir", stage_b="with_ir_corrected"):
    """Paired Kubescape analysis comparing two stages."""
    
    rows = []
    for stage in [stage_a, stage_b]:
        apps = results.get(stage, {}) or {}
        for app, metrics in apps.items():
            ks = metrics.get("kubescape", {}) or {}
            total = int(ks.get("total_controls", 0) or 0)
            if total <= 0:
                continue
            critical = int(ks.get("critical", 0) or 0)
            high = int(ks.get("high", 0) or 0)
            medium = int(ks.get("medium", 0) or 0)
            low = int(ks.get("low", 0) or 0)
            failed = critical + high + medium + low
            rows.append({
                "stage": stage,
                "app": app,
                "failed": failed,
                "total_controls": total,
                "fail_ratio": failed / total,
                "fail_pct": (failed / total) * 100,
            })
    
    if not rows:
        print("No Kubescape data found.")
        return pd.DataFrame()

    dfk = pd.DataFrame(rows)
    pivot = dfk.pivot(index="app", columns="stage", values="fail_ratio")
    if stage_a not in pivot.columns or stage_b not in pivot.columns:
        print(f"Missing data for {stage_a} or {stage_b}.")
        return dfk
    
    paired = pivot.dropna(subset=[stage_a, stage_b]).copy()
    paired = paired.rename(columns={stage_a: "ratio_a", stage_b: "ratio_b"})
    paired["delta"] = paired["ratio_b"] - paired["ratio_a"]
    n = len(paired)
    if n == 0:
        print(f"No paired apps between {stage_a} and {stage_b}.")
        return paired

    improved = (paired["delta"] < 0).sum()
    worsened = (paired["delta"] > 0).sum()
    unchanged = (paired["delta"] == 0).sum()
    print(f"\nPaired apps: {n} | Improved: {improved} ({improved/n:.1%}) | "
          f"Worsened: {worsened} ({worsened/n:.1%}) | Unchanged: {unchanged} ({unchanged/n:.1%})")

    try:
        stat, p = wilcoxon(paired["ratio_a"], paired["ratio_b"], zero_method="wilcox")
    except Exception:
        stat, p = np.nan, np.nan
    
    median_delta = paired["delta"].median()
    q1, q3 = paired["delta"].quantile([0.25, 0.75])
    r_rb = rank_biserial_from_wilcoxon(paired["delta"].values)
    print(f"Paired Wilcoxon {stage_a} → {stage_b}: n={n}, median Δ={median_delta:.4f}, "
          f"IQR=({q1:.4f}, {q3:.4f}), stat={stat}, p={p}, rank-biserial≈{r_rb:.3f}")

    human_stage_labels = {
        "without_ir": "Without IR",
        "with_ir": "With IR",
        "with_ir_corrected": "With IR Corrected",
        "with_overrides": "IR + Overrides",
        "with_overrides_corrected": "IR + Overrides Corrected"
    }
    label_a = human_stage_labels.get(stage_a, stage_a)
    label_b = human_stage_labels.get(stage_b, stage_b)

    zoom_needed = paired[["ratio_a","ratio_b"]].to_numpy().max() <= 0.30

    # Paired lines plot
    plt.figure(figsize=(9, max(4, n * 0.12)))
    apps_sorted = paired.sort_values("delta").index.tolist()
    for app in apps_sorted:
        a = paired.loc[app, "ratio_a"]
        b = paired.loc[app, "ratio_b"]
        color = "#2ecc71" if b < a else ("#e74c3c" if b > a else "#999999") # type: ignore
        plt.plot([0, 1], [a, b], marker="o", color=color, alpha=0.7, linewidth=1) # type: ignore
    plt.xticks([0, 1], [label_a, label_b], fontsize=11)
    plt.ylabel("Kubescape Misconfiguration Ratio")
    plt.title(f"Per-App Kubescape Change ({label_a} → {label_b})", fontsize=13, weight="bold")
    plt.ylim(0, 1.0 if not zoom_needed else 0.3)
    plt.tight_layout()
    fname = os.path.join(fig_dir, f"kubescape_paired_lines_{stage_a}_to_{stage_b}.png")
    plt.savefig(fname, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname)}")

    # Boxplot comparison
    df_sub = dfk[dfk["stage"].isin([stage_a, stage_b])].copy()
    plt.figure(figsize=(7, 5))
    sns.boxplot(data=df_sub, x="stage", y="fail_ratio", hue="stage",
                order=[stage_a, stage_b], palette="pastel", legend=False)
    plt.xticks([0, 1], [label_a, label_b], fontsize=11)
    plt.ylabel("Kubescape Misconfiguration Ratio")
    plt.xlabel("")
    plt.title(f"Kubescape Distribution: {label_a} vs {label_b}", fontsize=12, weight="bold")
    plt.ylim(0, 0.3 if zoom_needed else 1.0)
    plt.tight_layout()
    fname_box = os.path.join(fig_dir, f"kubescape_box_{stage_a}_vs_{stage_b}.png")
    plt.savefig(fname_box, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_box)}")

    return paired
