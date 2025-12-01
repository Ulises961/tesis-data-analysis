#!/usr/bin/env python3
"""
Human effort analysis: paired comparisons, delta histograms, and visualizations.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import wilcoxon


def analyze_human_effort(df, fig_dir):
    """
    Analyze human effort metrics for corrected stages, with paired comparisons
    and breakdown by edit type (added/removed/modified lines).
    """
    print("\n" + "="*80)
    print("HUMAN EFFORT ANALYSIS")
    print("="*80)

    base_corrected_pairs = [
        ("with_ir", "with_ir_corrected"),
        ("with_overrides", "with_overrides_corrected"),
    ]

    results_dict = {}
    for base_stage, corr_stage in base_corrected_pairs:
        print(f"\n--- Human Effort Summary ({corr_stage}) ---")
        corr_df = df[df["stage"] == corr_stage].copy()
        summary_cols = ["added_lines", "removed_lines", "modified_lines", "total_operations"]
        print(corr_df[summary_cols].describe().round(2).to_string())

        paired = df[df["stage"].isin([base_stage, corr_stage])].pivot(
            index="app", columns="stage", values="total_operations"
        ).dropna()

        if paired.empty or len(paired) < 3:
            print(f"Insufficient paired data for {base_stage} → {corr_stage}.")
            continue

        paired["delta"] = paired[corr_stage] - paired[base_stage]
        n = len(paired)
        median_delta = paired["delta"].median()

        try:
            stat, p = wilcoxon(paired[base_stage], paired[corr_stage], zero_method="wilcox")
        except Exception:
            stat, p = np.nan, np.nan

        print(f"Wilcoxon ({base_stage}→{corr_stage}): n={n}, median Δ={median_delta}, stat={stat}, p={p}")

        # Delta histogram
        plt.figure(figsize=(8, 5))
        plt.hist(paired["delta"], bins=20, color="steelblue", edgecolor="black", alpha=0.7)
        plt.axvline(median_delta, color="red", linestyle="--", linewidth=2, 
                   label=f"Median Δ={median_delta:.1f}")
        plt.xlabel("Δ Total Operations (corrected - base)", fontsize=11)
        plt.ylabel("Number of Apps", fontsize=11)
        plt.title(f"Change in Human Effort: {base_stage} → {corr_stage}", fontsize=12, weight="bold")
        plt.legend()
        plt.tight_layout()
        hist_path = os.path.join(fig_dir, f"delta_total_ops_{base_stage}_vs_{corr_stage}.png")
        plt.savefig(hist_path, dpi=300)
        plt.close()
        print(f"✓ Saved {os.path.basename(hist_path)}")

        # Scatter base vs corrected
        plt.figure(figsize=(7, 7))
        plt.scatter(paired[base_stage], paired[corr_stage], alpha=0.6, s=60, 
                   edgecolors="k", linewidths=0.5)
        max_val = max(paired[base_stage].max(), paired[corr_stage].max())
        plt.plot([0, max_val], [0, max_val], "r--", linewidth=2, label="y=x")
        plt.xlabel(f"{base_stage} Total Ops", fontsize=11)
        plt.ylabel(f"{corr_stage} Total Ops", fontsize=11)
        plt.title(f"Total Operations: {base_stage} vs {corr_stage}", fontsize=12, weight="bold")
        plt.legend()
        plt.tight_layout()
        scatter_path = os.path.join(fig_dir, f"scatter_total_ops_{base_stage}_vs_{corr_stage}.png")
        plt.savefig(scatter_path, dpi=300)
        plt.close()
        print(f"✓ Saved {os.path.basename(scatter_path)}")

        # Composition boxplot (added/removed/modified)
        df_melt = corr_df[["added_lines", "removed_lines", "modified_lines"]].melt(
            var_name="type", value_name="lines"
        )
        plt.figure(figsize=(7, 5))
        sns.boxplot(data=df_melt, x="type", y="lines", hue="type", palette="pastel", 
                    showfliers=False, legend=False)
        plt.xlabel("Edit Type", fontsize=11)
        plt.ylabel("Number of Lines", fontsize=11)
        plt.title(f"Human Edits Breakdown ({corr_stage})", fontsize=12, weight="bold")
        plt.xticks(rotation=15)
        plt.tight_layout()
        comp_path = os.path.join(fig_dir, f"human_edits_composition_{corr_stage}.png")
        plt.savefig(comp_path, dpi=300)
        plt.close()
        print(f"✓ Saved {os.path.basename(comp_path)}")

        results_dict[corr_stage] = {
            "paired": paired,
            "median_delta": median_delta,
            "wilcoxon_p": p,
        }

    return results_dict
