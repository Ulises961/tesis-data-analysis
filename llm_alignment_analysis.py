#!/usr/bin/env python3
"""
LLM vs human alignment analysis: F1, precision, recall, confusion matrices.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from utils import count_true


def analyze_llm_human_alignment(results, fig_dir):
    """
    Compare LLM expected_behaviour vs human assessments (tested_behaviour).
    Computes F1, precision, recall, and confusion matrices per stage.
    """
    print("\n" + "="*80)
    print("LLM-HUMAN ALIGNMENT ANALYSIS")
    print("="*80)

    records = []
    for stage, apps in results.items():
        for app, metrics in apps.items():
            llm_val = metrics.get("expected_behaviour")
            human_val = metrics.get("tested_behaviour")
            
            if llm_val is None or human_val is None:
                continue
            
            llm_bool = count_true(llm_val)
            human_bool = count_true(human_val)
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
        "with_ir_corrected": "With IR Corrected",
        "with_overrides": "IR + Overrides",
        "with_overrides_corrected": "IR + Overrides Corrected"
    }

    stage_order = ["without_ir", "with_ir", "with_ir_corrected", "with_overrides", "with_overrides_corrected"]
    stages_present = [s for s in stage_order if s in df_align["stage"].unique()]

    summary_rows = []
    for stage in stages_present:
        subset = df_align[df_align["stage"] == stage]
        y_true = subset["human_tested"].astype(bool)
        y_pred = subset["llm_expected"].astype(bool)
        
        agreement = (y_true == y_pred).sum()
        total = len(y_true)
        agreement_pct = (agreement / total * 100) if total > 0 else 0
        
        try:
            f1 = f1_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
        except Exception:
            f1, prec, rec = np.nan, np.nan, np.nan
        
        print(f"{human_labels.get(stage, stage):30s} | n={total:3d} | "
              f"Agreement={agreement_pct:5.1f}% | F1={f1:.3f} | Prec={prec:.3f} | Rec={rec:.3f}")
        
        summary_rows.append({
            "stage": stage,
            "stage_label": human_labels.get(stage, stage),
            "n": total,
            "agreement": agreement,
            "agreement_pct": agreement_pct,
            "f1": f1,
            "precision": prec,
            "recall": rec,
        })

    df_summary = pd.DataFrame(summary_rows)

    # Bar chart: F1, Precision, Recall
    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = np.arange(len(df_summary))
    width = 0.25

    ax.bar(x_pos - width, df_summary["f1"], width, label="F1 Score", color="#3498db")
    ax.bar(x_pos, df_summary["precision"], width, label="Precision", color="#2ecc71")
    ax.bar(x_pos + width, df_summary["recall"], width, label="Recall", color="#e74c3c")

    ax.set_ylabel("Score", fontsize=11, weight="bold")
    ax.set_xlabel("Stage", fontsize=11, weight="bold")
    ax.set_title("LLM-Human Alignment Metrics by Stage", fontsize=12, weight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df_summary["stage_label"], rotation=20, ha="right", fontsize=9)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fname_metrics = os.path.join(fig_dir, "llm_human_alignment_metrics.png")
    plt.savefig(fname_metrics, dpi=300)
    plt.close()
    print(f"\n✓ Saved {os.path.basename(fname_metrics)}")

    # Confusion matrix per stage
    n_stages = len(stages_present)
    fig_cm, axes = plt.subplots(1, n_stages, figsize=(4 * n_stages, 4))
    if n_stages == 1:
        axes = [axes]

    for ax, stage in zip(axes, stages_present):
        subset = df_align[df_align["stage"] == stage]
        y_true = subset["human_tested"].astype(bool)
        y_pred = subset["llm_expected"].astype(bool)
        
        cm = confusion_matrix(y_true, y_pred, labels=[False, True])
        
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
                    xticklabels=["Pred: False", "Pred: True"],
                    yticklabels=["True: False", "True: True"],
                    square=True, linewidths=1, linecolor="gray")
        ax.set_title(human_labels.get(stage, stage), fontsize=11, weight="bold")
        ax.set_xlabel("LLM Expected", fontsize=9)
        ax.set_ylabel("Human Tested", fontsize=9)

    plt.tight_layout()
    fname_cm = os.path.join(fig_dir, "llm_human_confusion_matrices.png")
    plt.savefig(fname_cm, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_cm)}")

    # Agreement percentage bar chart
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(range(len(df_summary)), df_summary["agreement_pct"], color="#9b59b6", alpha=0.8)
    ax.set_xticks(range(len(df_summary)))
    ax.set_xticklabels(df_summary["stage_label"], rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Agreement (%)", fontsize=11, weight="bold")
    ax.set_xlabel("Stage", fontsize=11, weight="bold")
    ax.set_title("LLM-Human Agreement Percentage", fontsize=12, weight="bold")
    ax.set_ylim(0, 100)
    for i, pct in enumerate(df_summary["agreement_pct"]):
        ax.text(i, pct + 2, f"{pct:.1f}%", ha="center", fontsize=9, weight="bold")
    plt.tight_layout()
    fname_agree = os.path.join(fig_dir, "llm_human_agreement_percentage.png")
    plt.savefig(fname_agree, dpi=300)
    plt.close()
    print(f"✓ Saved {os.path.basename(fname_agree)}")

    print("\n✓ LLM-human alignment analysis complete.\n")
    return df_align
