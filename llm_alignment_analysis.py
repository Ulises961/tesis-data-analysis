#!/usr/bin/env python3
"""
LLM vs Human Convergent Validity Analysis.

Compares two independent assessment methods:
- Human: Runtime behavior testing (ground truth)
- LLM: Static manifest analysis against repository intent

Metrics:
- Inter-rater reliability: Agreement %, Cohen's Kappa
- Predictive validity: F1, Precision, Recall (treating human as gold standard)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score, precision_score, recall_score, matthews_corrcoef
from utils import count_true


def analyze_llm_human_alignment(results, fig_dir):
    """
    Compare LLM static analysis vs human runtime testing.
    
    Two raters assessing the same applications through different evidence:
    - Human: Examines deployed runtime behavior
    - LLM: Analyzes manifests against repository documentation
    
    Convergence indicates manifest quality improvement.
    """
    print("\n" + "="*80)
    print("LLM-HUMAN CONVERGENT VALIDITY ANALYSIS")
    print("="*80)
    print("Human: Runtime behavior evaluation (ground truth)")
    print("LLM:   Static manifest-to-intent alignment prediction")
    print("="*80 + "\n")

    records = []
    for stage, apps in results.items():
        for app, metrics in apps.items():
            llm_val = metrics.get("llm_report",{}).get("aligned_to_intent")
            human_val = metrics.get("manual_review",{}).get("expected_behaviour")
            
            if llm_val is None or human_val is None:
                continue
            
            llm_bool = count_true(pd.Series(llm_val))
            human_bool = count_true(pd.Series(human_val))
            records.append({
                "stage": stage,
                "app": app,
                "llm_expected": llm_bool,
                "human_tested": human_bool,
            })

    if not records:
        print("No alignment data available.")
        return pd.DataFrame()

    df_align = pd.DataFrame(records)
    print(f"Loaded {len(df_align)} alignment records across {df_align['stage'].nunique()} stages.\n")

    human_labels = {
        "without_ir": "Without IR",
        "with_ir": "With IR",
        "with_ir_corrected": "With IR",
        "with_overrides": "IR + Overrides",
        "with_overrides_corrected": "IR + Overrides"
    }

    stage_order = ["without_ir", "with_ir", "with_ir_corrected", "with_overrides", "with_overrides_corrected"]
    stages_present = [s for s in stage_order if s in df_align["stage"].unique()]

    print("INTER-RATER RELIABILITY & PREDICTIVE VALIDITY")
    print("-" * 120)
    print(f"{'Stage':30s} | {'n':>3s} | {'Agree%':>7s} | {'Kappa':>7s} | {'MCC':>7s} | "
          f"{'F1':>6s} | {'Prec':>6s} | {'Rec':>6s} | {'LLM+%':>6s} | {'Human+%':>8s}")
    print("-" * 120)

    summary_rows = []
    for stage in stages_present:
        subset = df_align[df_align["stage"] == stage]
        y_true = subset["human_tested"].astype(bool)
        y_pred = subset["llm_expected"].astype(bool)
        
        agreement = (y_true == y_pred).sum()
        total = len(y_true)
        agreement_pct = (agreement / total * 100) if total > 0 else 0
        
        # Inter-rater reliability metrics
        try:
            kappa = cohen_kappa_score(y_true, y_pred)
        except Exception:
            kappa = np.nan
            
        try:
            mcc = matthews_corrcoef(y_true, y_pred)
        except Exception:
            mcc = np.nan
        
        # Predictive validity metrics (Human as ground truth)
        try:
            f1 = f1_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
        except Exception:
            f1, prec, rec = np.nan, np.nan, np.nan
        
        llm_pos_rate = (y_pred.sum() / total * 100) if total > 0 else 0
        human_pos_rate = (y_true.sum() / total * 100) if total > 0 else 0
        llm_pos_count = y_pred.sum()
        human_pos_count = y_true.sum()
        
        print(f"{human_labels.get(stage, stage):30s} | {total:3d} | "
              f"{agreement_pct:6.1f}% | {kappa:7.3f} | {mcc:7.3f} | "
              f"{f1:6.3f} | {prec:6.3f} | {rec:6.3f} | "
              f"{llm_pos_rate:5.1f}% | {human_pos_rate:7.1f}%")
        
        summary_rows.append({
            "stage": stage,
            "stage_label": human_labels.get(stage, stage),
            "n": total,
            "agreement": agreement,
            "agreement_pct": agreement_pct,
            "kappa": kappa,
            "mcc": mcc,
            "f1": f1,
            "precision": prec,
            "recall": rec,
            "llm_positive_rate": llm_pos_rate,
            "human_positive_rate": human_pos_rate,
            "llm_positive_count": llm_pos_count,
            "human_positive_count": human_pos_count,
            "llm_negative_count": total - llm_pos_count,
            "human_negative_count": total - human_pos_count,
        })

    df_summary = pd.DataFrame(summary_rows)
    print("-" * 120)
    print("\nInterpretation:")
    print("  • Agreement% & Kappa: Inter-rater reliability (convergence of independent assessments)")
    print("  • F1/Precision/Recall: Predictive validity (LLM's ability to predict runtime outcomes)")
    print("  • LLM+% vs Human+%: Positive prediction rates (reveals LLM optimism bias)")
    print("  • MCC: Correlation coefficient balanced for class imbalance\n")

    # Remove uninteresting stages for plotting
    df_summary = df_summary[df_summary["stage"].isin(["without_ir","with_ir_corrected", "with_overrides_corrected"])].reset_index(drop=True)
    if df_summary.empty:
        print("No stages with sufficient data for plotting.")
        return df_align
    # 1. LLM as Judge outcomes
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(len(df_summary))
    width = 0.35
    
    ax.bar(x_pos - width/2, df_summary["llm_positive_count"], width,
            label="Aligned to Intent", color="#2ecc71", alpha=0.8)
    ax.bar(x_pos + width/2, df_summary["llm_negative_count"], width,
            label="Not Aligned", color="#e74c3c", alpha=0.8)
    
    ax.set_ylabel("Number of Applications", fontsize=11, weight="bold")
    ax.set_xlabel("Stage", fontsize=11, weight="bold")
    ax.set_title("LLM as Judge: Static Analysis Results\n(Manifest-to-Intent Alignment)", 
                  fontsize=12, weight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df_summary["stage_label"], rotation=20, ha="right", fontsize=9)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylim(0, df_summary["n"].max() * 1.15)
    
    # Add percentage labels
    for i, row in df_summary.iterrows():
        total = row['n']
        pos_pct = (row['llm_positive_count'] / total * 100) if total > 0 else 0
        neg_pct = (row['llm_negative_count'] / total * 100) if total > 0 else 0
        ax.text(i - width/2, row['llm_positive_count'] + 0.2, f"{pos_pct:.0f} %", # type: ignore 
                ha='center', va='bottom', fontsize=8, weight='bold')
        ax.text(i + width/2, row['llm_negative_count'] + 0.2, f"{neg_pct:.0f} %", # type: ignore 
                ha='center', va='bottom', fontsize=8, weight='bold')
    
    plt.tight_layout()
    fname_llm = os.path.join(fig_dir, "llm_judge_outcomes.png")
    plt.savefig(fname_llm, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_llm)}")

    # 2. Human observed outcomes
    fig, ax = plt.subplots(figsize=(10, 6))
    



    x_pos = np.arange(len(df_summary))
    width = 0.35
    
    ax.bar(x_pos - width/2, df_summary["human_positive_count"], width,
            label="Works Correctly", color="#3498db", alpha=0.8)
    ax.bar(x_pos + width/2, df_summary["human_negative_count"], width,
            label="Fails/Issues", color="#e67e22", alpha=0.8)
    
    ax.set_ylabel("Number of Applications", fontsize=11, weight="bold")
    ax.set_xlabel("Stage", fontsize=11, weight="bold")
    ax.set_title("Human Testing: Runtime Behavior Results\n(Empirical Validation)", 
                  fontsize=12, weight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df_summary["stage_label"], rotation=20, ha="right", fontsize=9)
    ax.legend(fontsize=10, loc='upper left')
    ax.set_ylim(0, df_summary["n"].max() * 1.15)
    
    # Add percentage labels
    for i, row in df_summary.iterrows():
        total = row['n']
        pos_pct = (row['human_positive_count'] / total * 100) if total > 0 else 0
        neg_pct = (row['human_negative_count'] / total * 100) if total > 0 else 0
        ax.text(i - width/2, row['human_positive_count'] + 0.2, f"{pos_pct:.0f} %", # type: ignore 
                ha='center', va='bottom', fontsize=8, weight='bold')
        ax.text(i + width/2, row['human_negative_count'] + 0.2, f"{neg_pct:.0f} %", # type: ignore 
                ha='center', va='bottom', fontsize=8, weight='bold')
    
    plt.tight_layout()
    fname_human = os.path.join(fig_dir, "human_testing_outcomes.png")
    plt.savefig(fname_human, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_human)}")


    # 3. Confusion matrix per stage
    n_stages = len(stages_present)
    fig_cm, axes = plt.subplots(1, n_stages, figsize=(4 * n_stages, 4))
    if n_stages == 1:
        axes = [axes]

    for ax, stage in zip(axes, stages_present):
        subset = df_align[df_align["stage"] == stage]
        y_true = subset["human_tested"].astype(bool)
        y_pred = subset["llm_expected"].astype(bool)
        
        cm = confusion_matrix(y_pred, y_true, labels=[False, True])
        
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
                    xticklabels=["Fail", "Pass"],
                    yticklabels=["Fail", "Pass"],
                    square=True, linewidths=1, linecolor="gray")
        ax.set_title(human_labels.get(stage, stage), fontsize=11, weight="bold")
        ax.set_xlabel("Human: Runtime Behavior", fontsize=9, weight="bold")
        ax.set_ylabel("LLM: Static Analysis", fontsize=9, weight="bold")

    plt.tight_layout()
    fname_cm = os.path.join(fig_dir, "llm_human_confusion_matrices.png")
    plt.savefig(fname_cm, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_cm)}")

    print("\n✓ Convergent validity analysis complete.")
    print(f"  → As pipeline quality improves, static analysis increasingly predicts runtime outcomes\n")
    
    return df_align

