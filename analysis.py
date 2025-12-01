#!/usr/bin/env python3
"""
analysis.py

Main entry point for comprehensive Helm chart analysis.
Coordinates data loading, processing, and analysis across multiple modules.
"""

import argparse
import json
import os

# Import from our modular components
from utils import flatten_results
from plotting import ensure_fig_dir, plot_success_rates, plot_per_metric_success_rates
from statistical_tests import run_mcnemar_pairwise
from human_effort_analysis import analyze_human_effort
from effort_cluster_analysis import analyze_effort_vs_cluster
from kubescape_analysis import analyze_kubescape, analyze_kubescape_paired
from llm_alignment_analysis import analyze_llm_human_alignment
from repository_metadata import analyze_repository_metadata

# NEW IMPORT
from drift_quality_analysis import analyze_drift_quality


def main():
    """Main analysis workflow."""
    parser = argparse.ArgumentParser(description="Extended analysis for combined_metrics.json")
    parser.add_argument("path", type=str, help="Path to combined_metrics.json")
    parser.add_argument("--repo-csv", type=str, default="results/repositories_description.csv",
                       help="Path to repository metadata CSV")
    parser.add_argument("--diff-json", type=str, default="results/combined_special_diff_metrics.json",
                       help="Path to detailed diff metrics JSON")
    
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"File {args.path} not found.")
        return

    fig_dir = ensure_fig_dir("figures")

    # 1. Analyze Repository Metadata
    analyze_repository_metadata(args.repo_csv, fig_dir)

    # 2. Load Main Results
    with open(args.path, "r") as fh:
        results = json.load(fh)
    
    df = flatten_results(results)
    if df.empty:
        print("No rows extracted from JSON.")
        return

    # Compute Success Metrics
    df["fully_successful"] = (
        df["manifests_renderable"] & df["deployment_successful"] &
        df["pods_ready"] & df["services_accessible"]
    )
    stage_order = ["without_ir", "with_ir", "with_ir_corrected", "with_overrides", "with_overrides_corrected"]
    
    # 3. Standard Analysis
    success_rates = df.groupby("stage")["fully_successful"].mean().reindex(stage_order) * 100
    print("\n--- Success rates by stage (%) ---")
    print(success_rates.round(1).fillna(0).to_string())

    plot_success_rates(success_rates, fig_dir)
    plot_per_metric_success_rates(df, fig_dir)
    run_mcnemar_pairwise(df)
    analyze_human_effort(df, fig_dir)
    analyze_effort_vs_cluster(df, fig_dir)
    analyze_kubescape(results, fig_dir)
    analyze_kubescape_paired(results, fig_dir)
    analyze_llm_human_alignment(results, fig_dir)

    # 4. NEW: Drift Quality & ROI Analysis
    if os.path.exists(args.diff_json):
        analyze_drift_quality(args.diff_json, fig_dir)
    else:
        print(f"\n[Warning] Special diff file not found at {args.diff_json}. Skipping Drift Analysis.")

    print("\n" + "="*80)
    print("✓ Analysis complete. Figures saved in ./figures/")
    print("="*80)


if __name__ == "__main__":
    main()