import spelunk
from spelunk import (
    CaptureConfig,
    CaptureResult,
    ComparisonResult,
    DatasetRef,
    FeatureInspectionResult,
    LayerId,
    ModelRef,
    ReportResult,
    RunSummary,
    ScanResult,
    Session,
    SpelunkError,
    __version__,
    load_capture_config,
    run_capture_config,
)


def test_package_imports() -> None:
    assert __version__ == "0.0.0"


def test_public_api_exports_stable_entrypoints() -> None:
    exported = set(spelunk.__all__)

    assert Session.__name__ == "Session"
    assert CaptureConfig.__name__ == "CaptureConfig"
    assert CaptureResult.__name__ == "CaptureResult"
    assert ComparisonResult.__name__ == "ComparisonResult"
    assert FeatureInspectionResult.__name__ == "FeatureInspectionResult"
    assert ReportResult.__name__ == "ReportResult"
    assert RunSummary.__name__ == "RunSummary"
    assert ScanResult.__name__ == "ScanResult"
    assert DatasetRef.__name__ == "DatasetRef"
    assert ModelRef.__name__ == "ModelRef"
    assert LayerId("encoder") == "encoder"
    assert issubclass(SpelunkError, Exception)
    assert callable(load_capture_config)
    assert callable(run_capture_config)
    assert "Session" in exported
    assert "run_capture_config" in exported
    assert "NumpyShardActivationStore" not in exported
    assert "SpelunkApp" not in exported
