from dataclasses import dataclass


@dataclass(frozen=True)
class PrototypeRepairPlan:
    status: str
    failure_type: str
    steps: tuple[str, ...]
    constraints: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "failure_type": self.failure_type,
            "steps": list(self.steps),
            "constraints": list(self.constraints),
        }


def build_repair_plan(failure: dict | None) -> PrototypeRepairPlan:
    data = failure if isinstance(failure, dict) else {}
    failure_type = str(data.get("failure_type") or "unknown").strip()

    common = (
        "Inspect only the sandbox prototype files.",
        "Make the smallest change that addresses the recorded failure.",
        "Do not change NOVA core, security policy, credentials, or production files.",
        "Rerun the bounded smoke test and generated project tests after any change.",
    )

    steps_by_type = {
        "timeout": (
            "Identify the slowest test or code path from the recorded bounded output.",
            "Remove unnecessary work or reduce test scope without weakening the acceptance criteria.",
        ),
        "missing_dependency_or_import": (
            "Locate the missing import in the generated prototype or test file.",
            "Prefer the Python standard library or existing sandbox files; do not install packages.",
        ),
        "syntax_error": (
            "Locate the reported syntax error in the generated prototype or test file.",
            "Apply the smallest syntax correction and preserve the intended workflow.",
        ),
        "assertion_or_test_failure": (
            "Compare the failing assertion with the prototype's intended acceptance behavior.",
            "Fix the prototype behavior or test only when the test is demonstrably inconsistent with the build plan.",
        ),
        "test_collection_or_runtime_error": (
            "Inspect the bounded collection/runtime error details.",
            "Correct only the smallest sandbox-local defect causing collection or runtime failure.",
        ),
    }

    specific = steps_by_type.get(
        failure_type,
        (
            "Inspect the recorded failure details and identify a deterministic root cause.",
            "Prefer a minimal sandbox-local correction; do not broaden scope.",
        ),
    )

    return PrototypeRepairPlan(
        status="ready",
        failure_type=failure_type,
        steps=common[:1] + specific + common[1:],
        constraints=(
            "Sandbox only.",
            "No package installation or external side effects.",
            "No production workspace writes.",
            "No security-policy changes.",
            "No banking, payment, or credential actions.",
        ),
    )
