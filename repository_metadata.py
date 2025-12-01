#!/usr/bin/env python3
"""
Repository metadata analysis: CSV parsing, summary statistics, LaTeX table generation.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def analyze_repository_metadata(csv_path, fig_dir):
    """
    Analyze repository metadata from CSV file.
    Generates summary statistics, plots, and LaTeX table.
    """
    if not os.path.exists(csv_path):
        print(f"\nRepository metadata file not found: {csv_path}")
        return pd.DataFrame()

    print("\n" + "="*80)
    print("REPOSITORY METADATA ANALYSIS")
    print("="*80)

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} repositories from {os.path.basename(csv_path)}\n")
    
    if df.empty:
        print("No metadata records found.")
        return df

    # Summary statistics
    print("--- Summary Statistics ---")
    for col in ["stars", "forks", "watchers", "open_issues"]:
        if col in df.columns:
            print(f"{col.capitalize():15s}: mean={df[col].mean():.1f}, "
                  f"median={df[col].median():.0f}, max={df[col].max()}")

    # Language distribution
    if "language" in df.columns:
        lang_counts = df["language"].value_counts()
        print(f"\n--- Language Distribution (top {min(10, len(lang_counts))}) ---")
        print(lang_counts.head(10).to_string())
        
        plt.figure(figsize=(10, 6))
        top_langs = lang_counts.head(10)
        plt.barh(range(len(top_langs)), top_langs.values, color="#3498db") # type: ignore
        plt.yticks(range(len(top_langs)), top_langs.index, fontsize=10) # type: ignore
        plt.xlabel("Number of Repositories", fontsize=11, weight="bold")
        plt.title("Top 10 Programming Languages", fontsize=12, weight="bold")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        lang_path = os.path.join(fig_dir, "repository_languages.png")
        plt.savefig(lang_path, dpi=300)
        plt.close()
        print(f"✓ Saved {os.path.basename(lang_path)}")

    # Database distribution
    if "database" in df.columns:
        db_counts = df["database"].value_counts()
        print(f"\n--- Database Distribution ---")
        print(db_counts.to_string())
        
        if not db_counts.empty:
            plt.figure(figsize=(8, max(4, len(db_counts) * 0.4)))
            plt.barh(range(len(db_counts)), db_counts.values, color="#e74c3c") # type: ignore
            plt.yticks(range(len(db_counts)), db_counts.index, fontsize=10) # type: ignore
            plt.xlabel("Number of Repositories", fontsize=11, weight="bold")
            plt.title("Database Technologies", fontsize=12, weight="bold")
            plt.gca().invert_yaxis()
            plt.tight_layout()
            db_path = os.path.join(fig_dir, "repository_databases.png")
            plt.savefig(db_path, dpi=300)
            plt.close()
            print(f"✓ Saved {os.path.basename(db_path)}")

    # Stars distribution
    if "stars" in df.columns:
        plt.figure(figsize=(10, 6))
        plt.hist(df["stars"], bins=30, color="#2ecc71", alpha=0.7, edgecolor="black")
        plt.xlabel("Stars", fontsize=11, weight="bold")
        plt.ylabel("Frequency", fontsize=11, weight="bold")
        plt.title("Distribution of Repository Stars", fontsize=12, weight="bold")
        plt.tight_layout()
        stars_path = os.path.join(fig_dir, "repository_stars_distribution.png")
        plt.savefig(stars_path, dpi=300)
        plt.close()
        print(f"✓ Saved {os.path.basename(stars_path)}")

    # Generate LaTeX table
    latex_cols = ["full_name", "language", "database", "stars", "forks"]
    available_cols = [c for c in latex_cols if c in df.columns]
    
    if available_cols:
        df_latex = df[available_cols].copy()
        
        # Sort by stars descending, take top 20
        if "stars" in df_latex.columns:
            df_latex = df_latex.sort_values("stars", ascending=False).head(20)
        
        # Clean up full_name for LaTeX
        if "full_name" in df_latex.columns:
            df_latex["full_name"] = df_latex["full_name"].str.replace("_", r"\_")
        
        # Generate LaTeX string
        latex_str = df_latex.to_latex(index=False, escape=False, 
                                      column_format="l" * len(df_latex.columns))
        
        latex_path = os.path.join(fig_dir, "repository_metadata_table.tex")
        with open(latex_path, "w") as f:
            f.write(latex_str)
        print(f"✓ Saved LaTeX table to {os.path.basename(latex_path)}")

    print("\n✓ Repository metadata analysis complete.\n")
    return df
