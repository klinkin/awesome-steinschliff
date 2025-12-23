from __future__ import annotations

import json
import os
from pathlib import Path

from steinschliff.models import StructureInfo


def export_structures_json(*, services: dict[str, list[StructureInfo]], out_path: str) -> None:
    """Экспортирует структуры в JSON (для webapp)."""
    flat: list[dict[str, object]] = []
    for service, items in services.items():
        for s in items:
            tr = s.temperature[0] if s.temperature else None
            flat.append(
                {
                    "name": s.name,
                    "service": (s.service.name if s.service else service) or service,
                    "country": s.country or "",
                    "snow_type": (s.snow_type or "").strip(),
                    "temp_min": tr.get("min") if tr else None,
                    "temp_max": tr.get("max") if tr else None,
                    "tags": [t for t in (s.tags or []) if t],
                    "similars": [x for x in (s.similars or []) if x],
                    "features": [x for x in (s.features or []) if x],
                    "images": s.images or [],
                    "file_path": s.file_path,
                }
            )

    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)
