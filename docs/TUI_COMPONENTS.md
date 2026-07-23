# TUI Components

The Textual application is organized as reusable presentation components. Widgets call application services through screen/controller methods, not directly through storage, diagnostics, or framework adapters.

## Screens

- `ProjectPickerScreen`: default `spelunk` entry screen.
- `RunOverviewScreen`: summary of one run.
- `ScanScreen`: conclusions, diagnostics, and evidence.
- `LayerExplorerScreen`: layers and summaries.
- `FeatureExplorerScreen`: feature list and filters.
- `FeatureDetailScreen`: feature explanation, evidence, statistics.
- `CompareScreen`: run and checkpoint comparison.
- `ReportScreen`: Markdown and JSON report generation.
- `SettingsScreen`: local settings and themes.

## Persistent Widgets

- `HeaderBar`
- `Breadcrumbs`
- `NavigationTree`
- `DetailInspector`
- `StatusBar`
- `CommandPalette`
- `SearchOverlay`
- `ShortcutOverlay`
- `ProgressPanel`

## Messages

```python
RunOpened
LayerSelected
FeatureSelected
ScanRequested
ScanCompleted
CaptureStarted
CaptureProgressed
CaptureCompleted
ComparisonCompleted
ReportGenerated
ServiceFailed
CommandInvoked
```

Messages carry typed domain or service objects.

## State

```python
AppState:
    active_project
    current_run_id
    selected_layer_id
    selected_feature_id
    selected_checkpoint_id
    selected_mode
    breadcrumbs
    capture_status
    filters
    search_query
    theme
```

The state model stores IDs, view state, and summaries. It does not store framework models or raw activation arrays.
