from __future__ import annotations

import shutil
from pathlib import Path


def update_latest_json(source_path: Path, latest_path: Path) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"source JSON does not exist: {source_path}")
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, latest_path)
    return latest_path


def default_latest_path(output_dir: Path) -> Path:
    return output_dir / "latest.json"
