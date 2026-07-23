from spelunk.domain import (
    Checkpoint,
    CheckpointId,
    DatasetId,
    DatasetRef,
    DiagnosticId,
    DiagnosticResult,
    EvidenceItem,
    Layer,
    LayerId,
    ModelId,
    ModelRef,
    Provenance,
    Run,
    RunId,
    Statistic,
)


def test_domain_objects_are_typed_and_immutable() -> None:
    model = ModelRef(
        id=ModelId("model-001"),
        name="Tiny SAE",
        architecture_family="sparse-autoencoder",
        framework="pytorch",
    )
    dataset = DatasetRef(
        id=DatasetId("dataset-001"),
        name="sample",
        source_uri="file://sample.npy",
        kind="numpy",
    )
    checkpoint = Checkpoint(id=CheckpointId("ckpt-001"), label="step 100", step=100)
    run = Run(
        id=RunId("run-001"),
        model=model,
        dataset=dataset,
        storage_uri="run-001.spelunk",
        checkpoints=(checkpoint,),
    )

    assert run.model.id == "model-001"
    assert run.checkpoints[0].step == 100


def test_diagnostic_result_is_conclusion_first() -> None:
    layer = Layer(
        id=LayerId("encoder"),
        name="encoder",
        path="encoder",
        kind="linear",
        shape=(16, 8),
    )
    stat = Statistic(
        subject_id=layer.id,
        subject_type="layer",
        metric="inactive_fraction",
        value=0.25,
        sample_count=128,
        provenance=Provenance(source="unit-test"),
    )
    result = DiagnosticResult(
        id=DiagnosticId("activation-health"),
        name="Activation health",
        subject_id=layer.id,
        subject_type="layer",
        severity="warning",
        conclusion="Some features are inactive.",
        explanation="A non-trivial fraction of features did not activate in the sample.",
        evidence=(EvidenceItem(label="inactive_fraction", value="0.25"),),
        statistics=(stat,),
        provenance=Provenance(source="unit-test"),
    )

    assert result.conclusion
    assert result.evidence[0].label == "inactive_fraction"
    assert result.statistics[0].metric == "inactive_fraction"

