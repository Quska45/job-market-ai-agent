from __future__ import annotations

import hashlib
import json
from typing import Any


def build_content_hash(payload: dict[str, Any]) -> str:
    """Build a stable hash for deduplication and change detection."""
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

