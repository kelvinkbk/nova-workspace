from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class PrototypeFailure:
    status: str
    summary: str
    failure_type: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "summary": self.summary,
            "failure_type": self.failure_type,
            "details": list(self.details),
        }


def diagnose_project_test_failure(result: str) -> PrototypeFailure:
    text = str(result or "").strip()
    if not text:
        return PrototypeFailure(
            status="unknown",
            summary="No project-test result was recorded.",
            failure_type="missing_result",
        )

    lowered = text.lower()
    if "timed out" in lowered:
        return PrototypeFailure(
            status="failed",
            summary="Sandbox project tests exceeded the bounded timeout.",
            failure_type="timeout",
            details=[text[:1200]],
        )

    match = re.search(r"failed\s*\(exit code\s*(-?\d+)\)", lowered)
    exit_code = match.group(1) if match else "unknown"

    details = [line.strip() for line in text.splitlines() if line.strip()][-8:]
    failure_type = "assertion_or_test_failure"
    if "error" in lowered and "assert" not in lowered:
        failure_type = "test_collection_or_runtime_error"
    if "importerror" in lowered or "modulenotfounderror" in lowered:
        failure_type = "missing_dependency_or_import"
    elif "syntaxerror" in lowered:
        failure_type = "syntax_error"

    return PrototypeFailure(
        status="failed",
        summary=f"Project tests failed with exit code {exit_code}.",
        failure_type=failure_type,
        details=details,
    )
