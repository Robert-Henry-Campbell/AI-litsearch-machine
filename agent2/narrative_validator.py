from __future__ import annotations

import re
from typing import Sequence


SECTIONS: Sequence[str] = [
    "Search Overview",
    "Data Sources for Instrument Selection",
    "Differences in QTL Target",
    "SNP Selection Criteria and LD Clumping Thresholds",
    "Pleiotropy Checks and Sensitivity Analysis",
    "Final Assessment of Study Quality and Reliability",
]


def validate(markdown: str) -> bool:
    """Return True if ``markdown`` contains all required section headers."""
    pos = 0
    for title in SECTIONS:
        pattern = rf"^## {re.escape(title)}\s*$"
        match = re.search(pattern, markdown, flags=re.MULTILINE)
        if not match or match.start() < pos:
            return False
        pos = match.end()
    return True
