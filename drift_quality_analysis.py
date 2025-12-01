#!/usr/bin/env python3
"""
drift_quality_analysis.py

Analyzes configuration drift between Human-Authored and LLM-Generated manifests.
Implements a "Severity-Based" classification to demonstrate Error Reduction.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import wilcoxon

# Set style for academic charts
sns.set_theme(style="whitegrid")

def classify_issue(issue):
    """
    Classifies a discrepancy into Error, Enhancement, or Noise.
    
    Logic:
    1. TRUST THE REVIEW: If 'reviewed_level' exists, use it. 
       (e.g. A CRITICAL issue reviewed as INFO is Noise).
    2. IDENTIFY ENHANCEMENTS: Look for specific keywords in comments.
    3. DEFAULT TO NOISE: Unless it remains CRITICAL/HIGH, it is Noise.
    """
    # 1. Determine effective severity (Manual override takes precedence)
    severity = issue.get("reviewed_level") or issue.get("severity_level", "UNKNOWN")
    comment = issue.get("comments", "").lower()
    desc = issue.get("severity_description", "").lower()
    issue_type = issue.get("issue_type", "").lower()
    path = issue.get("path", "").lower()

    # 2. Check for Enhancements (Production/Security upgrades)
    # Only if it's an ADDITION or explicit upgrade comment
    if "enhancement" in comment or "production ready" in comment:
        return "Enhancement"
    
    # Security additions (e.g., adding securityContext) are Enhancements
    if "security" in desc and "extra" in issue_type:
        return "Enhancement"
    
    # Probes are enhancements if added
    if ("readinessprobe" in path or "livenessprobe" in path) and "extra" in issue_type:
        return "Enhancement"

    # 3. Check for Errors (Functionality Breakers)
    # Only count as Error if it remains CRITICAL/HIGH after review
    if severity in ["CRITICAL", "HIGH"]:
        # Exclude known benign patterns even if marked high
        if "correctly mapped" in comment:
            return "Noise"
        if "local image" in comment:
            return "Noise"
        if "different name" in comment:
            return "Noise" # Usually implies structural change, not functional break
            
        return "Error"

    # 4. Everything else is Noise (Stylistic drift, defaults, explicit config)
    return "Noise"

def analyze_drift_quality(json_path, fig_dir):
    print("\n" + "="*60)
    print("CONFIGURATION DRIFT & ERROR REDUCTION ANALYSIS")
    print("="*60)

    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Flatten Data
    records = []
    for stage, apps in data.items():
        for app_name, details in apps.items():
            if "issues_by_severity" in details:
                for severity, issues in details["issues_by_severity"].items():
                    for issue in issues:
                        category = classify_issue(issue)
                        records.append({
                            "stage": stage,
                            "app": app_name,
                            "original_severity": severity,
                            "reviewed_severity": issue.get("reviewed_level", severity),
                            "category": category
                        })

    df = pd.DataFrame(records)
    
    # Define logical order
    stage_order = ["without_ir", "with_ir", "with_overrides"]
    existing_stages = [s for s in stage_order if s in df["stage"].unique()]
    df["stage"] = pd.Categorical(df["stage"], categories=existing_stages, ordered=True)

    # --- 1. Generate Statistics ---
    stats = df.groupby(["stage", "category"], observed=False).size().unstack(fill_value=0)
    
    # Ensure all columns exist
    for col in ["Error", "Noise", "Enhancement"]:
        if col not in stats.columns:
            stats[col] = 0
    
    # Calculate apps per stage for normalization
    apps_per_stage = df.groupby("stage")["app"].nunique()
    
    # Normalized stats (per app)
    stats_normalized = stats.div(apps_per_stage, axis=0)
    
    print("\n--- Raw Drift Counts ---")
    print(stats)
    print(f"\nApps per stage: {apps_per_stage.to_dict()}")
    
    print("\n--- Normalized Drift per Application ---")
    print(stats_normalized.round(2))

    # --- Statistical Tests: Wilcoxon Signed-Rank for Paired Comparisons ---
    print("\n" + "="*60)
    print("STATISTICAL SIGNIFICANCE TESTS")
    print("="*60)
    
    # Get per-app error and total drift counts for each stage
    error_counts = df[df["category"] == "Error"].groupby(["stage", "app"]).size().unstack(fill_value=0)
    total_drift_counts = df.groupby(["stage", "app"]).size().unstack(fill_value=0)
    
    # Test 1: Error count comparison (without_ir vs with_overrides)
    if "without_ir" in error_counts.index and "with_overrides" in error_counts.index:
        # Get common apps between both stages
        common_apps = list(set(error_counts.columns) & set(error_counts.columns))
        
        baseline_errors = error_counts.loc["without_ir", common_apps].values # type: ignore
        final_errors = error_counts.loc["with_overrides", common_apps].values # type: ignore
        
        # Wilcoxon signed-rank test (paired)
        try:
            stat, p_value = wilcoxon(baseline_errors, final_errors, zero_method='wilcox', alternative='greater')
            print(f"\n--- Wilcoxon Test: Error Count Reduction ---")
            print(f"Comparison: without_ir vs with_overrides")
            print(f"Apps tested: {len(common_apps)}")
            print(f"Baseline errors (per app): {baseline_errors}")
            print(f"Final errors (per app): {final_errors}")
            print(f"Statistic: {stat:.2f}")
            print(f"p-value: {p_value:.4f}")
            if p_value < 0.05: # type: ignore
                print(f"Result: ✓ Significant error reduction (p < 0.05)")
            else:
                print(f"Result: Not statistically significant (p >= 0.05)")
        except Exception as e:
            print(f"\n--- Wilcoxon Test: Error Count ---")
            print(f"Could not perform test: {e}")
    
    # Test 2: Total drift comparison (without_ir vs with_overrides)
    if "without_ir" in total_drift_counts.index and "with_overrides" in total_drift_counts.index:
        common_apps = list(set(total_drift_counts.columns) & set(total_drift_counts.columns))
        
        baseline_drift = total_drift_counts.loc["without_ir", common_apps].values # type: ignore
        final_drift = total_drift_counts.loc["with_overrides", common_apps].values # type: ignore
        
        try:
            stat, p_value = wilcoxon(baseline_drift, final_drift, zero_method='wilcox', alternative='two-sided')
            print(f"\n--- Wilcoxon Test: Total Drift Count ---")
            print(f"Comparison: without_ir vs with_overrides")
            print(f"Apps tested: {len(common_apps)}")
            print(f"Baseline drift (per app): {baseline_drift}")
            print(f"Final drift (per app): {final_drift}")
            print(f"Statistic: {stat:.2f}")
            print(f"p-value: {p_value:.4f}")
            if p_value < 0.05: # type: ignore
                print(f"Result: ✓ Significant difference in drift (p < 0.05)")
            else:
                print(f"Result: No significant difference in total drift (p >= 0.05)")
        except Exception as e:
            print(f"\n--- Wilcoxon Test: Total Drift ---")
            print(f"Could not perform test: {e}")
    
    # Calculate Error Reduction Rate (using normalized per-app values)
    print("\n" + "="*60)
    if "without_ir" in stats_normalized.index and "with_overrides" in stats_normalized.index:
        base_err_per_app = stats_normalized.loc["without_ir", "Error"]
        final_err_per_app = stats_normalized.loc["with_overrides", "Error"]
        
        # Raw counts for reference
        base_err_raw = stats.loc["without_ir", "Error"]
        final_err_raw = stats.loc["with_overrides", "Error"]
        
        if base_err_per_app > 0: # type: ignore
            reduction = ((base_err_per_app - final_err_per_app) / base_err_per_app) * 100 # type: ignore
            print(f"[Key Finding] Error Reduction Rate (Normalized): {reduction:.1f}%")
            print(f"  Per-app errors: {base_err_per_app:.2f} -> {final_err_per_app:.2f}")
            print(f"  Raw counts: {base_err_raw} -> {final_err_raw}")
        else:
             print("[Key Finding] Baseline had 0 detected errors in sample.")

    # --- 2. Visualization: The "Clean Up" Chart ---
    # Stacked Bar Chart showing the composition
    plt.figure(figsize=(10, 6))
    
    # Colors: Red=Error, Gray=Noise, Green=Enhancement
    colors = {"Error": "#e74c3c", "Noise": "#95a5a6", "Enhancement": "#2ecc71"}
    # Relabel columns to ensure consistent order
    stats = stats[["Error", "Enhancement", "Noise"]]
    # Relabel stages for better readability

    # Convert to a pandas Index to satisfy static type checkers
    stats.index = pd.Index([s.replace("_", " ").title() for s in stats.index])

    stats.plot(kind='bar', stacked=True, 
               color=[colors.get(c, '#333') for c in stats.columns], 
               figsize=(9, 6), width=0.7)
    
    plt.title("Semantic Composition of Configuration Drift", fontsize=14)
    plt.ylabel("Number of Discrepancies", fontsize=12)
    plt.xlabel("Experimental Stage", fontsize=12)
    plt.xticks(rotation=0)
    plt.legend(title="Drift Category")
    plt.tight_layout()
    
    plot_path = os.path.join(fig_dir, "semantic_drift_composition.png")
    plt.savefig(plot_path, dpi=300)
    print(f"✓ Saved plot to {plot_path}")
    plt.close()

    # --- 3. Visualization: The "Signal Only" Chart (Optional but strong) ---
    # Show ONLY Errors to emphasize the drop
    plt.figure(figsize=(8, 5))
    if "Error" in stats.columns:
        stats["Error"].plot(kind='bar', color='#e74c3c', width=0.6)
        plt.title("Reduction in Deployment-Blocking Errors", fontsize=14)
        plt.ylabel("Count of Critical Errors", fontsize=12)
        plt.xlabel("")
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        err_plot_path = os.path.join(fig_dir, "error_reduction_trend.png")
        plt.savefig(err_plot_path, dpi=300)
        print(f"✓ Saved plot to {err_plot_path}")
        plt.close()
    
    # --- 4. Normalized Comparison Chart ---
    plt.figure(figsize=(10, 6))
    
    # Reorder columns to match color scheme: Error, Enhancement, Noise
    stats_normalized_ordered = stats_normalized[["Error", "Enhancement", "Noise"]]
    
    # Relabel stages for readability
    stats_normalized_ordered.index = pd.Index([s.replace("_", " ").title() for s in stats_normalized_ordered.index])
    
    stats_normalized_ordered.plot(kind='bar', stacked=True,
                                   color=[colors.get(c, '#333') for c in stats_normalized_ordered.columns],
                                   figsize=(9, 6), width=0.7)
    
    plt.title("Normalized Drift per Application", fontsize=14)
    plt.ylabel("Drift Entries per Application", fontsize=12)
    plt.xlabel("Experimental Stage", fontsize=12)
    plt.xticks(rotation=0)
    plt.legend(title="Drift Category")
    plt.tight_layout()
    
    norm_plot_path = os.path.join(fig_dir, "drift_normalized_per_app.png")
    plt.savefig(norm_plot_path, dpi=300)
    print(f"✓ Saved plot to {norm_plot_path}")
    plt.close()

if __name__ == "__main__":
    # Example usage
    analyze_drift_quality("results/combined_special_diff_metrics.json", "figures")