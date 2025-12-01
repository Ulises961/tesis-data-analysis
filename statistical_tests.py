#!/usr/bin/env python3
"""
Statistical testing functions (McNemar, Mann-Whitney, Wilcoxon, etc.).
"""

import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.contingency_tables import mcnemar


def run_mcnemar_pairwise(df):
    """
    Run pairwise McNemar tests comparing fully_successful between stage pairs.
    
    Args:
        df: DataFrame with columns ['stage', 'app', 'fully_successful']
    """
    print("\n--- McNemar pairwise ---")

    def run_between(s1, s2):
        sub = df[df["stage"].isin([s1, s2])].pivot(
            index="app", columns="stage", values="fully_successful"
        )
        sub = sub.dropna()
        if sub.empty:
            print(f"McNemar {s1} vs {s2}: no paired apps.")
            return
        
        table = pd.crosstab(sub[s1].astype(int), sub[s2].astype(int))
        if table.shape == (2, 2):
            res = mcnemar(table, exact=True)
            b = table.iloc[0, 1]
            c = table.iloc[1, 0]
            print(f"McNemar {s1} vs {s2}: b={b}, c={c}, p={res.pvalue:.6g}") # type: ignore
        else:
            print(f"{s1} vs {s2}: insufficient variability.")

    pairs = [
        ("without_ir", "with_ir"),
        ("with_ir", "with_ir_corrected"),
        ("with_overrides", "with_overrides_corrected"),
        ("with_ir", "with_overrides"),
    ]
    
    for a, b in pairs:
        if {a, b}.issubset(df["stage"].unique()):
            run_between(a, b)


def print_mwu(label, grp_success, grp_fail):
    """Print Mann-Whitney U test result for two groups."""
    from utils import rank_biserial_u
    
    if (len(grp_success) >= 2) and (len(grp_fail) >= 2):
        u, p = mannwhitneyu(grp_success, grp_fail, alternative="two-sided")
        r = rank_biserial_u(u, len(grp_success), len(grp_fail))
        print(f"\n{label} Mann–Whitney: U={u:.1f}, p={p:.6g}, rank-biserial={r:.3f}")
    else:
        print(f"\n{label}: insufficient data for Mann–Whitney test.")
