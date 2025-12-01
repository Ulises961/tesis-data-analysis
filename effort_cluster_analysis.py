#!/usr/bin/env python3
"""
Analysis of human effort vs cluster size relationships.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, linregress
from matplotlib.patches import Patch


def analyze_effort_vs_cluster(df, fig_dir):
    """Analyze relationship between cluster size (total lines) and human effort."""
    
    stages = ["with_ir_corrected", "with_overrides_corrected"]
    sel = df[df["stage"].isin(stages)].copy()
    sel = sel[(sel["cluster_lines"] > 0) & (sel["total_operations"] > 0)]
    
    if sel.empty:
        print("No data for effort vs cluster analysis.")
        return

    print(f"\n{'='*80}")
    print("HUMAN EFFORT vs CLUSTER SIZE ANALYSIS")
    print(f"{'='*80}")
    print(f"Analyzing {len(sel)} apps across {sel['stage'].nunique()} corrected stages.\n")

    # Compute Spearman correlation
    rho, p = spearmanr(sel["cluster_lines"], sel["total_operations"])
    print(f"Overall Spearman ρ = {rho:.3f}, p = {p:.3g}")

    for stage in stages:
        stage_data = sel[sel["stage"] == stage]
        if len(stage_data) >= 3:
            rho_s, p_s = spearmanr(stage_data["cluster_lines"], stage_data["total_operations"])
            print(f"  {stage}: n={len(stage_data)}, Spearman ρ={rho_s:.3f}, p={p_s:.3g}")

    colors = {"with_ir_corrected": "#3498db", "with_overrides_corrected": "#e74c3c"}
    markers = {"with_ir_corrected": "o", "with_overrides_corrected": "s"}
    
    # Plot 1: Log-log scatter with regression
    fig, ax = plt.subplots(figsize=(9, 6))
    
    for stage in stages:
        stage_data = sel[sel["stage"] == stage]
        ax.scatter(stage_data["cluster_lines"], stage_data["total_operations"],
                  c=colors[stage], marker=markers[stage], s=60, alpha=0.7,
                  edgecolors="black", linewidths=0.5,
                  label=stage.replace("_", " ").title())
    
    log_x = np.log10(sel["cluster_lines"])
    log_y = np.log10(sel["total_operations"])
    slope, intercept, r_val, p_val, std_err = linregress(log_x, log_y)
    
    x_fit = np.logspace(np.log10(sel["cluster_lines"].min()), 
                        np.log10(sel["cluster_lines"].max()), 100)
    y_fit = 10 ** (intercept + slope * np.log10(x_fit))
    
    ax.plot(x_fit, y_fit, 'k--', linewidth=2, alpha=0.8, 
            label=f'Power law: slope={slope:.2f}, R²={r_val**2:.2f}') # type: ignore
    
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Cluster Size (Total Lines of YAML)", fontsize=12, weight="bold")
    ax.set_ylabel("Human Effort (Total Operations)", fontsize=12, weight="bold")
    ax.set_title("Human Effort Scales with Cluster Complexity", fontsize=13, weight="bold")
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, which="both", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "effort_vs_cluster_loglog.png"), dpi=300)
    plt.close()
    print(f"✓ Saved effort_vs_cluster_loglog.png")

    # Plot 2: Top 20 apps by effort
    top_apps = sel.nlargest(20, "total_operations")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = np.arange(len(top_apps))
    
    ax.barh(y_pos, top_apps["total_operations"], 
           color=[colors[s] for s in top_apps["stage"]],
           edgecolor="black", linewidth=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_apps["app"], fontsize=9)
    ax.set_xlabel("Total Operations (Human Edits)", fontsize=11, weight="bold")
    ax.set_title("Top 20 Apps by Human Effort", fontsize=12, weight="bold")
    ax.invert_yaxis()
    
    for i, (idx, row) in enumerate(top_apps.iterrows()):
        ax.text(row["total_operations"] + 2, i, 
                f'{int(row["cluster_lines"])} lines',
                va='center', fontsize=8, style='italic', color='gray')
    
    legend_elements = [
        Patch(facecolor=colors["with_ir_corrected"], label="With IR Corrected"),
        Patch(facecolor=colors["with_overrides_corrected"], label="With Overrides Corrected")
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "effort_top_apps.png"), dpi=300)
    plt.close()
    print(f"✓ Saved effort_top_apps.png")

    # Plot 3: Binned analysis
    sel["cluster_category"] = pd.cut(
        sel["cluster_lines"],
        bins=[0, 100, 500, 1000, 5000, float('inf')],
        labels=["<100", "100-500", "500-1K", "1K-5K", ">5K"]
    )
    
    fig, ax = plt.subplots(figsize=(9, 6))
    
    for stage in stages:
        stage_data = sel[sel["stage"] == stage]
        grouped = stage_data.groupby("cluster_category", observed=True)["total_operations"].mean()
        
        ax.plot(grouped.index.astype(str), grouped.values, 
               marker=markers[stage], color=colors[stage], linewidth=2,
               markersize=8, label=stage.replace("_", " ").title())
    
    ax.set_xlabel("Cluster Size Category (Lines of YAML)", fontsize=11, weight="bold")
    ax.set_ylabel("Average Human Effort (Total Operations)", fontsize=11, weight="bold")
    ax.set_title("Human Effort by Cluster Size Category", fontsize=12, weight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "effort_by_cluster_category.png"), dpi=300)
    plt.close()
    print(f"✓ Saved effort_by_cluster_category.png")
    
    print(f"\n{'='*80}\n")
