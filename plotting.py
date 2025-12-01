#!/usr/bin/env python3
"""
Plotting functions for visualization of analysis results.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def ensure_fig_dir(path="figures"):
    """Create figures directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path


def plot_success_rates(success, fig_dir):
    """Plot overall success rates by stage as a bar chart."""
    labels = {
        "without_ir": "Without IR",
        "with_ir": "With IR",
        "with_ir_corrected": "With IR Corrected",
        "with_overrides": "IR With Overrides",
        "with_overrides_corrected": "IR With Overrides Corrected",
    }
    success = success.rename(index=labels)
    
    plt.figure(figsize=(8, 5))
    colors = sns.color_palette("viridis", n_colors=len(success))
    x = list(range(len(success)))
    bars = plt.bar(x, success.values, color=colors)
    plt.ylim(0, 100)
    plt.ylabel("Success Rate (%)")
    plt.xticks(x, success.index)
    plt.gca().set_xticklabels(success.index, rotation=0)
    
    # Annotate values above bars
    for rect, v in zip(bars, success.values):
        plt.text(rect.get_x() + rect.get_width() / 2, v + 1, f"{v:.1f}%", 
                ha="center", va="bottom")
    
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "deployment_success_rates.png"), dpi=300)
    plt.close()


def plot_per_metric_success_rates(df, fig_dir):
    """Plot success rates broken down by individual metrics and stages."""
    metrics_config = [
        ("manifests_renderable", "Manifests Renderable"),
        ("deployment_successful", "Deployment Successful"),
        ("expected_behaviour", "Tested Behaviour"),
    ]
    stage_order = [
        "without_ir", "with_ir", "with_ir_corrected",
        "with_overrides", "with_overrides_corrected"
    ]
    labels = {
        "without_ir": "Without IR",
        "with_ir": "With IR",
        "with_ir_corrected": "With IR Corrected",
        "with_overrides": "IR With Overrides",
        "with_overrides_corrected": "IR With Overrides Corrected",
    }

    metric_success = []
    for stage in stage_order:
        st_df = df[df["stage"] == stage]
        if st_df.empty:
            continue
        for key, label in metrics_config:
            if key in st_df.columns:
                rate = st_df[key].mean() * 100
                metric_success.append({
                    "stage": labels[stage],
                    "metric": label,
                    "success_rate": rate,
                })

    if not metric_success:
        print("No per-metric success data.")
        return

    rates_df = pd.DataFrame(metric_success)
    
    # Print per-metric success rates to console
    print("\n" + "="*80)
    print("PER-METRIC SUCCESS RATES BY STAGE")
    print("="*80)
    
    for metric_key, metric_label in metrics_config:
        print(f"\n--- {metric_label} (%) ---")
        metric_data = rates_df[rates_df["metric"] == metric_label]
        if not metric_data.empty:
            for _, row in metric_data.iterrows():
                print(f"{row['stage']:30s}: {row['success_rate']:6.1f}%")
        else:
            print("  No data available")
    
    print("="*80 + "\n")
    
    # Plot
    plt.figure(figsize=(12, 7))
    sns.barplot(data=rates_df, x="metric", y="success_rate", hue="stage", 
                hue_order=list(labels.values()), palette="Spectral")
    plt.ylabel("Success Rate (%)")
    plt.xlabel("Metrics")
    plt.ylim(0, 100)
    plt.legend(title="Stage", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.title("Success Rates by Metric and Stage")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "per_metric_success_rates.png"), dpi=300)
    plt.close()
