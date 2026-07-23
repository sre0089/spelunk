import sys


def test_domain_import_does_not_load_ui_or_framework_modules() -> None:
    import spelunk.domain  # noqa: F401

    forbidden = {"rich", "textual", "typer", "torch"}
    assert forbidden.isdisjoint(sys.modules)
