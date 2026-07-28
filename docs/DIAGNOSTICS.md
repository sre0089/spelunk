# Diagnostics

Spelunk diagnostics summarize activation health for each captured layer. The first built-in diagnostic checks whether stored activations look usable for inspection and comparison.

## Activation Health

The activation health diagnostic reports:

- `zero_fraction`: fraction of activation elements near zero
- `dead_feature_fraction`: fraction of feature columns that are consistently inactive or constant
- `saturation_fraction`: fraction of activation elements above the saturation threshold
- `outlier_fraction`: fraction of activation elements with very large z-scores
- `maximum_abs`: largest absolute activation value seen

Severity levels are:

- `info`: no obvious activation health issue
- `warning`: sparse activations, dead features, or outliers worth inspecting
- `critical`: whole-layer inactivity, heavy saturation, or a high dead-feature fraction

These diagnostics are meant to catch capture mistakes and representation pathologies before release analysis. They do not replace model-specific evaluation.
