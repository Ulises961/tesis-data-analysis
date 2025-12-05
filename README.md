# Analysis Code - Complete Guide

## Quick Start

```bash
# Navigate to analysis directory
cd "/home/ulises/Documents/UniTn/2nd Year/2 semester/Tirocinio/Analysis"

# Activate virtual environment
source .venv/bin/activate

# Run full analysis
python3 analysis.py 'results/combined_metrics.json' --repo-csv 'results/repositories_description.csv'

# Check output
ls figures/
```

## Project Structure

```
Analysis/
├── analysis.py                      (86 lines)   - Main entry point
├── analysis_old.py                  (1239 lines) - Original monolithic backup
│
├── Core Modules
│   ├── utils.py                     (107 lines)  - Data processing utilities
│   ├── plotting.py                  (114 lines)  - General visualization
│   └── statistical_tests.py         (59 lines)   - Statistical test wrappers
│
├── Domain Analysis Modules
│   ├── human_effort_analysis.py     (113 lines)  - Paired effort analysis
│   ├── effort_cluster_analysis.py   (138 lines)  - Cluster size relationships
│   ├── kubescape_analysis.py        (290 lines)  - Security vulnerability
│   ├── llm_alignment_analysis.py    (164 lines)  - LLM vs human
│   └── repository_metadata.py       (114 lines)  - Repository characteristics
│
├── Documentation
│   ├── README_CODE_STRUCTURE.md     - Architecture overview
│   ├── MODULE_REFERENCE.md          - Quick function reference
│   ├── REFACTORING_SUMMARY.md       - Before/after comparison
│   └── README.md                    - This file
│
├── Data & Config
│   ├── requirements.txt             - Python dependencies
│   └── results/
│       ├── combined_metrics.json    - Main analysis data
│       └── repositories_description.csv - Metadata
│
└── Output
    └── figures/                     - Generated plots and CSVs
```

## Module Overview

### Main Entry Point
**`analysis.py`** - Orchestrates entire analysis workflow
- Loads JSON data
- Converts to DataFrame
- Runs all analysis modules in sequence
- Saves outputs to `./figures/`

### Core Utilities
**`utils.py`** - Shared helper functions
- `flatten_results()` - JSON → DataFrame conversion
- `safe_get()` - Safe nested dict access
- `rank_biserial_*()` - Effect size calculations
- `count_true()` - Boolean counting

**`plotting.py`** - General visualization
- `ensure_fig_dir()` - Create output directory
- `plot_success_rates()` - Overall success bars
- `plot_per_metric_success_rates()` - Per-metric grouped bars

**`statistical_tests.py`** - Test wrappers
- `run_mcnemar_pairwise()` - Paired categorical comparisons
- `print_mwu()` - Mann-Whitney U test formatter

### Domain Analyses
**`human_effort_analysis.py`**
- **Purpose**: Compare human effort between base and corrected stages
- **Tests**: Wilcoxon signed-rank (paired continuous)
- **Plots**: Histograms, scatter plots, composition boxplots
- **Output**: 4 figures per stage pair 
**`effort_cluster_analysis.py`**
- **Purpose**: Relationship between effort and cluster size
- **Tests**: Spearman correlation, linear regression
- **Plots**: Log-log scatter, top-20 bar, binned categories
- **Output**: 3 figures with power-law fits

**`kubescape_analysis.py`**
- **Purpose**: Security vulnerability analysis
- **Tests**: Mann-Whitney U (unpaired), Wilcoxon (paired)
- **Plots**: Bar charts, boxplots, paired line plots
- **Output**: Multiple figures

**`llm_alignment_analysis.py`**
- **Purpose**: LLM vs human agreement
- **Metrics**: F1 score, precision, recall, agreement %
- **Plots**: Metrics bar chart, confusion matrices
- **Output**: 3 figures

**`repository_metadata.py`**
- **Purpose**: Repository characteristics
- **Analyses**: Language/database distribution, stars
- **Plots**: Horizontal bar charts, histograms
- **Output**: 3+ figures + LaTeX table

## Data Flow

```
1. Load Data
   combined_metrics.json → analysis.py

2. Process
   flatten_results() → pandas DataFrame

3. Analyze
   ├── Plot success rates
   ├── Run McNemar tests
   ├── Analyze human effort
   ├── Analyze cluster relationships
   ├── Analyze Kubescape security
   ├── Analyze LLM alignment
   └── Analyze repository metadata

4. Output
   figures/ directory (PNGfiles)
```

## Output Files

### Visualizations (PNG)
**Success Rates**
- `success_rates_by_stage.png`
- `per_metric_success_rates.png`

**Human Effort**
- `human_effort_delta_histogram_*.png`
- `human_effort_scatter_*.png`
- `human_effort_composition_boxplot_*.png`

**Cluster Analysis**
- `effort_vs_cluster_scatter.png`
- `top20_apps_by_effort.png`
- `effort_by_cluster_bin.png`

**Kubescape**
- `kubescape_vulnerability_ratio_by_stage.png`
- `kubescape_vulnerability_distribution.png`
- `kubescape_paired_lines_*.png`
- `kubescape_box_*.png`

**LLM Alignment**
- `llm_human_alignment_metrics.png`
- `llm_human_confusion_matrices.png`
- `llm_human_agreement_percentage.png`

**Repository Metadata**
- `repository_languages.png`
- `repository_databases.png`
- `repository_stars_distribution.png`
- `repository_metadata_table.tex` (LaTeX)

## Common Tasks

### Run Full Analysis
```bash
source .venv/bin/activate
python3 analysis.py 'results/combined_metrics.json' --repo-csv 'results/repositories_description.csv'
```

### Run Specific Analysis
```python
import json
from utils import flatten_results
from kubescape_analysis import analyze_kubescape
from plotting import ensure_fig_dir

with open("results/combined_metrics.json") as f:
    results = json.load(f)

fig_dir = ensure_fig_dir("custom_output")
analyze_kubescape(results, fig_dir)
```

### Test Module Imports
```bash
python3 -c "from utils import flatten_results; print('✓')"
python3 -c "from plotting import plot_success_rates; print('✓')"
python3 -c "from kubescape_analysis import analyze_kubescape; print('✓')"
```

### Check Line Counts
```bash
wc -l *.py
```

## Key Features

### Statistical Tests
- **McNemar's Test**: Paired categorical data (success/failure across stages)
- **Wilcoxon Signed-Rank**: Paired continuous data (human effort base → corrected)
- **Mann-Whitney U**: Unpaired continuous data (Kubescape across stages)
- **Spearman Correlation**: Monotonic relationships (effort vs cluster size)

### Effect Sizes
- **Rank-biserial correlation**: For Mann-Whitney U and Wilcoxon tests
- **Median differences**: For Kubescape comparisons
- **Cohen's kappa → F1/precision/recall**: For LLM alignment (replaced per user request)

### Visualizations
- Publication-quality figures (300 DPI)
- Consistent color schemes
- Clear annotations and labels
- Error bars where appropriate
- Zoomed views for concentrated data

## Dependencies

Install via `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key packages:
- `numpy`, `pandas` - Data processing
- `matplotlib`, `seaborn` - Plotting
- `scipy` - Statistical tests
- `statsmodels` - McNemar test
- `scikit-learn` - ML metrics

## Troubleshooting

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies if needed
pip install -r requirements.txt
```

### Missing Data Files
```bash
# Check data files exist
ls results/combined_metrics.json
ls results/repositories_description.csv
```

### No Figures Generated
```bash
# Check figures directory exists and has content
ls -la figures/
```

## Development

### Adding New Analysis
1. Create new module file (e.g., `new_analysis.py`)
2. Define analysis function with signature: `def analyze_new(df, fig_dir)`
3. Import in `analysis.py`: `from new_analysis import analyze_new`
4. Add to main() workflow: `analyze_new(df, fig_dir)`

### Modifying Existing Analysis
1. Locate relevant module (use MODULE_REFERENCE.md)
2. Edit function in module
3. Test independently before running full analysis
4. Verify output in `figures/` directory

## References

- **README_CODE_STRUCTURE.md** - Complete architecture documentation
- **MODULE_REFERENCE.md** - Function signatures and imports

## Contact & Support

For questions about:
- **Code structure**: See README_CODE_STRUCTURE.md
- **Function usage**: See MODULE_REFERENCE.md

