from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    field: str | None = None


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def error(self, code: str, message: str, field: str | None = None) -> None:
        self.issues.append(Issue("error", code, message, field))

    def warning(self, code: str, message: str, field: str | None = None) -> None:
        self.issues.append(Issue("warning", code, message, field))

    def merge(self, other: "ValidationReport") -> None:
        self.issues.extend(other.issues)
        self.details.update(other.details)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [asdict(issue) for issue in self.issues],
            "details": self.details,
        }
