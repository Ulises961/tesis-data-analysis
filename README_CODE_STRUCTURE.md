# Analysis Code Structure

## Overview
The analysis codebase has been refactored from a single monolithic file (~1200 lines) into a modular architecture with specialized components. This improves maintainability, testability, and code clarity.

## Module Organization

### Core Modules

#### `analysis.py` (Main Entry Point)
- **Purpose**: Coordinates the entire analysis workflow
- **Key Functions**: `main()` - argument parsing, data loading, orchestration
- **Usage**: `python3 analysis.py 'results/combined_metrics.json' --repo-csv 'results/repositories_description.csv'`

#### `utils.py` (Core Utilities)
- **Purpose**: Shared utility functions for data processing
- **Key Functions**:
  - `safe_get()` - Safe nested dictionary traversal
  - `rank_biserial_u()` - Effect size calculation for Mann-Whitney U
  - `rank_biserial_from_wilcoxon()` - Effect size for Wilcoxon test
  - `flatten_results()` - Converts nested JSON to DataFrame
  - `count_true()` - Boolean/string counting helper

#### `plotting.py` (Visualization)
- **Purpose**: General-purpose plotting functions
- **Key Functions**:
  - `ensure_fig_dir()` - Creates output directory
  - `plot_success_rates()` - Overall success rate bar chart
  - `plot_per_metric_success_rates()` - Per-metric grouped bar charts with console output

#### `statistical_tests.py` (Statistical Testing)
- **Purpose**: Statistical test wrappers
- **Key Functions**:
  - `run_mcnemar_pairwise()` - Paired McNemar tests for 4 stage comparisons
  - `print_mwu()` - Mann-Whitney U test wrapper with formatted output

### Domain-Specific Analysis Modules

#### `human_effort_analysis.py`
- **Purpose**: Human effort paired comparison analysis
- **Analyses**:
  - Wilcoxon signed-rank tests (paired continuous data)
  - Delta histograms (base → corrected)
  - Scatter plots with diagonal reference
  - Composition boxplots (added/removed/modified lines)
- **Output**: 4 figures per stage pair + CSV exports

#### `effort_cluster_analysis.py`
- **Purpose**: Relationship between human effort and cluster size
- **Analyses**:
  - Spearman correlation (monotonic relationships)
  - Log-log regression (power-law fitting)
  - Top-20 apps by effort bar chart
  - Binned category analysis (small/medium/large clusters)
- **Output**: 3 figures with statistical annotations

#### `kubescape_analysis.py`
- **Purpose**: Security vulnerability analysis using Kubescape metrics
- **Analyses**:
  - `analyze_kubescape()` - Unpaired Mann-Whitney U tests across all stages
  - `analyze_kubescape_paired()` - Paired Wilcoxon tests with line plots
  - Vulnerability percentage calculations (converted from ratios)
  - Distribution boxplots and bar charts
- **Output**: Multiple figures + CSV results

#### `llm_alignment_analysis.py`
- **Purpose**: LLM vs human alignment analysis
- **Analyses**:
  - F1 score, precision, recall calculations
  - Confusion matrices per stage
  - Agreement percentage analysis
- **Output**: 3 figures + summary CSV

#### `repository_metadata.py`
- **Purpose**: Repository characteristics analysis
- **Analyses**:
  - Language distribution (top 10)
  - Database technology counts
  - Stars distribution histogram
  - LaTeX table generation (top 20 repos)
- **Output**: 3+ figures + LaTeX table

## Data Flow

```
combined_metrics.json → analysis.py → flatten_results()
                                    ↓
                            pandas DataFrame
                                    ↓
        ┌───────────────────────────┴───────────────────────────┐
        ↓                           ↓                           ↓
   Plotting               Statistical Tests          Domain Analyses
   - Success rates        - McNemar                - Human effort
   - Per-metric charts    - Mann-Whitney U         - Cluster analysis
                          - Wilcoxon               - Kubescape
                                                   - LLM alignment
                                                   - Repository metadata
                                    ↓
                            figures/ directory
                            (PNG files + CSV exports)
```

## Output Structure

All outputs are saved to `./figures/` directory:

### Statistical Results (CSV)
- `mcnemar_pairwise_results.csv` - McNemar test results
- `human_effort_paired_*.csv` - Paired human effort data
- `kubescape_mann_whitney_results.csv` - Kubescape comparisons
- `llm_human_alignment_summary.csv` - LLM alignment metrics

### Visualizations (PNG)
- Success rate charts (overall + per-metric)
- Human effort analyses (histograms, scatter, boxplots)
- Cluster size relationships (scatter, bar, binned)
- Kubescape vulnerability charts (bar, boxplot, paired lines)
- LLM alignment (metrics bar, confusion matrices, agreement)
- Repository metadata (languages, databases, stars)

### LaTeX Output
- `repository_metadata_table.tex` - LaTeX table of top repositories

## Key Improvements

1. **Maintainability**: Each module has a clear, focused purpose
2. **Testability**: Individual functions can be tested independently
3. **Readability**: ~100-300 lines per module vs. 1200+ monolithic file
4. **Extensibility**: New analyses can be added as separate modules
5. **Documentation**: Comprehensive docstrings in each module
6. **Imports**: Clean dependency structure with no circular imports

## Dependencies

All modules share common dependencies:
- `numpy`, `pandas` - Data processing
- `matplotlib`, `seaborn` - Visualization
- `scipy.stats` - Statistical tests
- `sklearn.metrics` - ML metrics (F1, precision, recall, confusion matrix)

## Running the Analysis

```bash
# Full analysis with all stages
python3 analysis.py 'results/combined_metrics.json' --repo-csv 'results/repositories_description.csv'

# Without repository metadata
python3 analysis.py 'results/combined_metrics.json'
```

## Backward Compatibility

The refactored code produces **identical output** to the original monolithic version:
- Same figure filenames
- Same CSV structure
- Same console output format
- Same statistical tests and results

The old version is preserved as `analysis_old.py` for reference.
