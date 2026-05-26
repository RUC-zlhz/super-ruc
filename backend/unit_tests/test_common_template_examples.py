from __future__ import annotations

from pathlib import Path

from scripts import import_common_template_examples as importer


def _write_required_templates(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for filename in importer._required_template_filenames():
        (root / filename).write_bytes(b"template")


def test_template_root_env_override(monkeypatch, tmp_path):
    root = tmp_path / "custom-templates"
    _write_required_templates(root)
    monkeypatch.setenv("COMMON_TEMPLATE_EXAMPLE_ROOT", str(root))
    importer.get_template_example_root.cache_clear()

    assert importer.get_template_example_root() == root


def test_template_root_docker_docs_candidate(monkeypatch, tmp_path):
    root = tmp_path / "docs" / "source" / "common-templates"
    _write_required_templates(root)
    monkeypatch.delenv("COMMON_TEMPLATE_EXAMPLE_ROOT", raising=False)
    monkeypatch.setattr(importer, "_candidate_template_roots", lambda: [root])
    importer.get_template_example_root.cache_clear()

    assert importer.assert_template_example_files_available() == root


def test_template_root_local_docs_fallback(monkeypatch):
    monkeypatch.delenv("COMMON_TEMPLATE_EXAMPLE_ROOT", raising=False)
    importer.get_template_example_root.cache_clear()

    root = importer.get_template_example_root()

    assert root.name == "common-templates"
    assert not importer._missing_template_files(root)
