#!/usr/bin/env python3
"""
Utility functions for data processing and calculations.
"""

import numpy as np
import pandas as pd


def safe_get(d, *keys, default=None):
    """Safely traverse nested dictionaries."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def rank_biserial_u(u_stat, n1, n2):
    """Calculate rank-biserial correlation from Mann-Whitney U statistic."""
    try:
        return 1.0 - (2.0 * u_stat) / (n1 * n2)
    except Exception:
        return np.nan


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


def count_true(series):
    """Count TRUE values in a series (handles both bool and string)."""
    if series.dtype == bool:
        return series.sum()
    else:
        return (series.astype(str).str.upper() == "TRUE").sum()


def flatten_results(results):
    """
    Flatten nested JSON results into a DataFrame with per-app metrics.
    
    Args:
        results: Nested dict with structure {stage: {app: {metrics}}}
    
    Returns:
        pd.DataFrame with flattened metrics per app/stage
    """
    rows = []
    for stage, apps in results.items():
        for app, metrics in apps.items():
            # Support multiple possible human-effort keys depending on stage/name variations
            he = {}
            he_source = None
            for candidate in ("human_effort_ir", "human_effort_overrides", "human_effort", "human-effort"):
                if candidate in metrics:
                    he = metrics.get(candidate, {}) or {}
                    he_source = candidate
                    break
            
            sk = metrics.get("skaffold", {}) or {}
            llm = metrics.get("llm_report", {}) or {}
            manual = metrics.get("manual_review", {}) or {}

            def total_lines(key):
                val = he.get(key, {})
                if isinstance(val, dict):
                    return val.get("total", 0)
                if isinstance(val, (int, float)):
                    return int(val)
                return 0

            # Record which human-effort candidate we used to aid debugging
            rows.append({
                "stage": stage,
                "app": app,
                "manifests_renderable": bool(safe_get(sk, "manifests_renderable", default=False)),
                "deployment_successful": bool(safe_get(sk, "deployment_successful", default=False)),
                "pods_ready": bool(safe_get(sk, "pods_ready", default=False)),
                "services_accessible": bool(safe_get(sk, "services_accessible", default=False)),
                "llm_aligned_to_intent": bool(safe_get(llm, "aligned_to_intent", default=False)),
                "expected_entrypoint": bool(safe_get(manual, "expected_entrypoint", default=False)),
                "expected_behaviour": bool(safe_get(manual, "expected_behaviour", default=False)),
                "added_lines": total_lines("added_lines"),
                "removed_lines": total_lines("removed_lines"),
                "modified_lines": total_lines("modified_lines"),
                "total_operations": total_lines("total_operations") if (he and ("total_operations" in he)) else 0,
                "kubescape_critical": int(safe_get(metrics, "kubescape", "critical", default=0) or 0),
                "kubescape_high": int(safe_get(metrics, "kubescape", "high", default=0) or 0),
                "kubescape_medium": int(safe_get(metrics, "kubescape", "medium", default=0) or 0),
                "kubescape_low": int(safe_get(metrics, "kubescape", "low", default=0) or 0),
                "kubescape_total_controls": int(safe_get(metrics, "kubescape", "total_controls", default=0) or 0),
                "cluster_lines": int(safe_get(metrics, "cluster_lines", default=0) or 0),
                "he_source": he_source,
            })
    
    return pd.DataFrame(rows)
