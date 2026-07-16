from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


def save_models_json(path: Path, models: list[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [model.model_dump(mode="json") for model in models]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

