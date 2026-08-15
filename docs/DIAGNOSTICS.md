# Diagnostics

Spelunk runs lightweight checks over captured activations so obvious capture problems show up quickly. The first built-in check is activation health.

## Activation Health

Activation health looks at each captured layer and asks: do these activations look useful to inspect?

It reports five values:

- `zero_fraction`: how many activation values are basically zero
- `dead_feature_fraction`: how many feature columns are inactive or constant
- `saturation_fraction`: how many values are very large
- `outlier_fraction`: how many values are unusually far from the layer average
- `maximum_abs`: the largest absolute value seen

## How The Checks Work

Spelunk reads activation batches from disk and treats each layer separately.

For `zero_fraction`, it counts values close to zero and divides by the total number of activation values. If a layer has 100 activation values and 97 are near zero, the zero fraction is `0.97`.

For `dead_feature_fraction`, Spelunk looks down each feature column across samples. A feature is considered dead if it is near zero for almost every sample or if it never changes. If a layer has 10 features and 3 are dead, the dead feature fraction is `0.3`.

For `saturation_fraction`, Spelunk counts values whose absolute value is above the saturation threshold. This is a quick way to catch layers that may be exploding or clipped.

For `outlier_fraction`, Spelunk compares values against the layer's mean and standard deviation. A value far beyond the normal spread is counted as an outlier. This is not a model-quality judgment; it is a warning that the layer may be worth inspecting.

## Severity

- `info`: nothing obvious was found
- `warning`: sparse activations, dead features, or outliers were detected
- `critical`: the whole layer appears inactive, heavily saturated, or has many dead features

Diagnostics are meant to point you toward suspicious layers. They do not replace evaluation metrics, loss curves, or task-specific analysis.
