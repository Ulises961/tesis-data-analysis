# Quick Module Reference

## Module Import Guide

### For New Analysis Scripts

If you want to create a new analysis script, import from these modules:

```python
# Core utilities
from utils import safe_get, flatten_results, rank_biserial_u, count_true

# Plotting utilities
from plotting import ensure_fig_dir, plot_success_rates, plot_per_metric_success_rates

# Statistical tests
from statistical_tests import run_mcnemar_pairwise, print_mwu

# Domain-specific analyses (use as needed)
from human_effort_analysis import analyze_human_effort
from effort_cluster_analysis import analyze_effort_vs_cluster
from kubescape_analysis import analyze_kubescape, analyze_kubescape_paired
from llm_alignment_analysis import analyze_llm_human_alignment
from repository_metadata import analyze_repository_metadata
```

## Function Quick Reference

### `utils.py`
```python
safe_get(dict, *keys, default=None)          # Navigate nested dicts safely
flatten_results(results)                      # JSON → DataFrame conversion
rank_biserial_u(u_stat, n1, n2)              # Effect size for Mann-Whitney
rank_biserial_from_wilcoxon(deltas)          # Effect size for Wilcoxon
count_true(series)                            # Count TRUE values (bool or str)
```

### `plotting.py`
```python
ensure_fig_dir(path="figures")                # Create output directory
plot_success_rates(success, fig_dir)          # Overall success bar chart
plot_per_metric_success_rates(df, fig_dir)    # Per-metric grouped bars
```

### `statistical_tests.py`
```python
run_mcnemar_pairwise(df)                      # McNemar for 4 stage pairs
print_mwu(label, grp_success, grp_fail)       # Mann-Whitney U wrapper
```

### `human_effort_analysis.py`
```python
analyze_human_effort(df, fig_dir)             # Full paired effort analysis
# Produces: histograms, scatter plots, boxplots, Wilcoxon tests
```

### `effort_cluster_analysis.py`
```python
analyze_effort_vs_cluster(df, fig_dir)        # Effort vs cluster size
# Produces: Spearman correlation, log-log plots, binned analysis
```

### `kubescape_analysis.py`
```python
analyze_kubescape(results, fig_dir)           # Unpaired Kubescape analysis
analyze_kubescape_paired(results, fig_dir,    # Paired Kubescape comparison
                         stage_a, stage_b)
```

### `llm_alignment_analysis.py`
```python
analyze_llm_human_alignment(results, fig_dir) # LLM vs human analysis
# Produces: F1/precision/recall, confusion matrices, agreement %
```

### `repository_metadata.py`
```python
analyze_repository_metadata(csv_path, fig_dir) # Repository characteristics
# Produces: language/database charts, stars distribution, LaTeX table
```

## Common Usage Patterns

### Loading Data
```python
import json
with open("results/combined_metrics.json") as f:
    results = json.load(f)

from utils import flatten_results
df = flatten_results(results)
```

### Creating Figures Directory
```python
from plotting import ensure_fig_dir
fig_dir = ensure_fig_dir("figures")  # Creates ./figures/
```

### Running Full Analysis Pipeline
```python
# See analysis.py main() function for complete example
from plotting import plot_success_rates, plot_per_metric_success_rates
from statistical_tests import run_mcnemar_pairwise
from human_effort_analysis import analyze_human_effort
# ... etc.

# Run analyses in sequence
plot_success_rates(success_rates, fig_dir)
run_mcnemar_pairwise(df)
analyze_human_effort(df, fig_dir)
# ... etc.
```

### Custom Analysis Example
```python
#!/usr/bin/env python3
import json
from utils import flatten_results
from plotting import ensure_fig_dir
from kubescape_analysis import analyze_kubescape

# Load data
with open("results/combined_metrics.json") as f:
    results = json.load(f)

# Setup
fig_dir = ensure_fig_dir("custom_figures")

# Run specific analysis
df = flatten_results(results)
analyze_kubescape(results, fig_dir)
```

## Testing Individual Modules

You can test each module independently:

```bash
# Test if modules import correctly
python3 -c "from utils import flatten_results; print('✓ utils')"
python3 -c "from plotting import plot_success_rates; print('✓ plotting')"
python3 -c "from statistical_tests import run_mcnemar_pairwise; print('✓ statistical_tests')"
python3 -c "from human_effort_analysis import analyze_human_effort; print('✓ human_effort_analysis')"
python3 -c "from effort_cluster_analysis import analyze_effort_vs_cluster; print('✓ effort_cluster_analysis')"
python3 -c "from kubescape_analysis import analyze_kubescape; print('✓ kubescape_analysis')"
python3 -c "from llm_alignment_analysis import analyze_llm_human_alignment; print('✓ llm_alignment_analysis')"
python3 -c "from repository_metadata import analyze_repository_metadata; print('✓ repository_metadata')"
```

## Module Dependencies

```
analysis.py
    ├── utils.py (no dependencies)
    ├── plotting.py
    │   └── uses: matplotlib, seaborn, pandas
    ├── statistical_tests.py
    │   └── uses: utils.py, scipy.stats, statsmodels
    ├── human_effort_analysis.py
    │   └── uses: utils.py, matplotlib, seaborn, scipy.stats
    ├── effort_cluster_analysis.py
    │   └── uses: matplotlib, seaborn, scipy.stats
    ├── kubescape_analysis.py
    │   └── uses: utils.py, matplotlib, seaborn, scipy.stats
    ├── llm_alignment_analysis.py
    │   └── uses: utils.py, matplotlib, seaborn, sklearn.metrics
    └── repository_metadata.py
        └── uses: pandas, matplotlib
```

## Notes

- All modules use **absolute imports** (no relative imports)
- No circular dependencies between modules
- Each module is self-contained and can be imported independently
- All matplotlib figures are saved with `dpi=300` for publication quality
- Console output uses formatted tables for readability
