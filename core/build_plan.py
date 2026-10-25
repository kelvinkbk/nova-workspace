from dataclasses import dataclass


@dataclass(frozen=True)
class BuildPlan:
    title: str
    objective: str
    deliverables: tuple[str, ...]
    files: tuple[str, ...]
    implementation_steps: tuple[str, ...]
    test_strategy: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    constraints: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "objective": self.objective,
            "deliverables": list(self.deliverables),
            "files": list(self.files),
            "implementation_steps": list(self.implementation_steps),
            "test_strategy": list(self.test_strategy),
            "acceptance_criteria": list(self.acceptance_criteria),
            "constraints": list(self.constraints),
            "status": "ready",
            "scaffold_path": None,
        }


def compile_build_plan(build_spec: dict | None) -> BuildPlan | None:
    if not isinstance(build_spec, dict):
        return None

    title = str(build_spec.get("title") or "Untitled product").strip()
    scope = tuple(str(item).strip() for item in (build_spec.get("mvp_scope") or []) if str(item).strip())
    scope = scope or ("one narrowly scoped workflow",)

    return BuildPlan(
        title=title,
        objective=(
            f"Build only the smallest testable version of '{title}' that addresses "
            "the validated problem and produces one measurable demand signal."
        ),
        deliverables=(
            "Minimal implementation for the validated workflow.",
            "Automated tests for the core behavior.",
            "A minimal usage/readme note explaining the test path.",
        ),
        files=(
            "app/",
            "tests/",
            "README.md",
        ),
        implementation_steps=(
            "Create the smallest implementation around the validated problem.",
            f"Implement only the scoped workflows: {', '.join(scope)}.",
            "Add deterministic tests before expanding functionality.",
            "Run the test suite and keep the first build reproducible.",
            "Prepare the smallest permitted distribution/test path.",
        ),
        test_strategy=(
            "Unit-test the core workflow and its edge cases.",
            "Verify the success metric can be observed without paid dependencies.",
            "Run the existing NOVA test suite before any release decision.",
        ),
        acceptance_criteria=(
            "The scoped workflow works end-to-end in a reproducible local test.",
            "The build stays within the stated zero-cost constraint.",
            "No extra feature is added unless required by the validated problem.",
            "The success metric is measurable.",
        ),
        constraints=tuple(str(item) for item in (build_spec.get("known_constraints") or [])),
    )
