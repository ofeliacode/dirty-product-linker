# Dirty Product Linker

Production-oriented product extraction and entity linking from noisy Russian, English, and transliterated text.

The project now includes its first executable milestone: versioned Pydantic data
contracts and validated sample JSONL records. See [SPEC.md](SPEC.md) for the complete
architecture and [docs/data-contract.md](docs/data-contract.md) for the implemented
catalog and annotation formats.

Planned interfaces:

- Python library
- batch CLI
- FastAPI inference service
- reproducible training and evaluation pipeline

No quality metrics are claimed before the test split is frozen and the baseline is executed.

## Current verification

Create a Python 3.12 virtual environment and install the development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
PYTHONPATH=src .venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src
```

The sample catalog is intentionally small. It validates the format and category
coverage; it is not used to claim model quality.
