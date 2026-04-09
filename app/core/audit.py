from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("nutriscan.audit")


def audit_log(event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        **fields,
    }
    logger.info(json.dumps(payload, default=str, sort_keys=True))
