from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent
SKILL_ROOTS = (
    REPOSITORY_ROOT / "skills" / "100x-learning",
    REPOSITORY_ROOT / "skills" / "private-knowledge",
    REPOSITORY_ROOT / "skills" / "content-system",
)

for skill_root in reversed(SKILL_ROOTS):
    sys.path.insert(0, str(skill_root))
