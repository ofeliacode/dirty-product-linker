import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_promotion_cli_requires_explicit_human_confirmation(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts/promote_multi_product_holdout.py"),
            "--candidates",
            str(PROJECT_ROOT / "data/benchmark/candidates/multi_product_v0_1.jsonl"),
            "--output",
            str(tmp_path / "reviewed.jsonl"),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--reviewer",
            "ofeliacode",
            "--reviewed-at",
            "2026-07-16",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-all is required" in result.stderr
    assert not (tmp_path / "reviewed.jsonl").exists()
