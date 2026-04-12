from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

FRAMEWORK_NAME = "Constructive Accessibility Instrument v0.3"
CITATION_TEXT = (
    "If you use this instrument or measurement framing, please cite: "
    "M.R. Nothem (2026), Constructive Accessibility from Committed Prefixes in Random 3-SAT."
)
FRAMEWORK_TAG = "Nothem Constructive Accessibility Instrument v0.3"
USAGE_NOTICE = (
    "Copyright 2026 Michael R. Nothem / Reachability Labs. "
    "Licensed under the Apache License, Version 2.0. "
    "See NOTICE file for attribution requirements. https://reachabilitylabs.org"
)


def provenance(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "_framework": FRAMEWORK_NAME,
        "_framework_tag": FRAMEWORK_TAG,
        "_citation": CITATION_TEXT,
        "_usage_notice": USAGE_NOTICE,
        "_generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        base.update(extra)
    return base


def write_companion_meta(path: str | Path, extra: Dict[str, Any] | None = None) -> None:
    target = Path(path)
    meta_path = target.with_suffix(target.suffix + '.meta.json')
    meta_path.write_text(json.dumps(provenance(extra), indent=2), encoding='utf-8')


PLOT_FOOTER = "Reachability Labs • Constructive Accessibility Instrument • cite Nothem (2026)"
