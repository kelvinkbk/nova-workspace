from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class WorkingMemory:
    current_goal: str | None = None
    current_task: str | None = None
    active_project: str | None = None
    notes: list[str] = field(default_factory=list)
    plan_steps: list[str] = field(default_factory=list)
    plan_index: int = 0
    plan_goal: str | None = None
    last_action: str | None = None
    last_action_result: str | None = None
    last_reflection: str | None = None
    candidate_urls: list[str] = field(default_factory=list)
    candidate_index: int = 0
    opportunity_evidence: list[dict] = field(default_factory=list)
    selected_opportunity: dict | None = None
    search_queries: list[str] = field(default_factory=list)
    research_updated_at: str | None = None
    source_history: list[dict] = field(default_factory=list)
    opportunity_synthesis: list[dict] = field(default_factory=list)
    validation_plan: dict | None = None
    build_decision: dict | None = None
    build_spec: dict | None = None
    build_plan: dict | None = None

    def set_goal(self, goal: str) -> None:
        self.current_goal = goal

    def set_task(self, task: str) -> None:
        self.current_task = task

    def set_project(self, project: str) -> None:
        self.active_project = project

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def clear_task(self) -> None:
        self.current_task = None

    def reset_research_state(self) -> None:
        """Clear transient opportunity-research state while preserving the goal."""
        self.current_task = "Begin a fresh opportunity research cycle"
        self.candidate_urls = []
        self.candidate_index = 0
        self.opportunity_evidence = []
        self.opportunity_synthesis = []
        self.validation_plan = None
        self.build_decision = None
        self.build_spec = None
        self.build_plan = None
        self.selected_opportunity = None
        self.search_queries = []
        self.last_action = None
        self.last_action_result = None
        self.last_reflection = None
        self.research_updated_at = None

    def touch_research_state(self) -> None:
        self.research_updated_at = datetime.now(timezone.utc).isoformat()

    def research_state_stale(self, max_age_hours: float = 2.0) -> bool:
        if not (
            self.candidate_urls
            or self.opportunity_evidence
            or self.selected_opportunity
            or self.search_queries
            or self.validation_plan
        ):
            return False
        if not self.research_updated_at:
            return not bool(self.validation_plan)
        try:
            updated = datetime.fromisoformat(self.research_updated_at)
        except ValueError:
            return True
        return datetime.now(timezone.utc) - updated > timedelta(hours=max_age_hours)

    def set_plan(self, steps: list[str], goal: str | None = None) -> None:
        cleaned = [step.strip() for step in steps if isinstance(step, str) and step.strip()]
        self.plan_steps = cleaned
        self.plan_index = 0
        self.plan_goal = goal or self.current_goal
        self.current_task = cleaned[0] if cleaned else self.current_task

    def advance_plan(self) -> None:
        if not self.plan_steps:
            return
        if self.plan_index < len(self.plan_steps) - 1:
            self.plan_index += 1
            self.current_task = self.plan_steps[self.plan_index]
        else:
            self.plan_index = len(self.plan_steps)
            self.current_task = None

    def has_active_plan(self) -> bool:
        return bool(self.plan_steps) and self.plan_index < len(self.plan_steps)

    def to_dict(self) -> dict:
        return {
            "current_goal": self.current_goal,
            "current_task": self.current_task,
            "active_project": self.active_project,
            "notes": self.notes.copy(),
            "plan_steps": self.plan_steps.copy(),
            "plan_index": self.plan_index,
            "plan_goal": self.plan_goal,
            "last_action": self.last_action,
            "last_action_result": self.last_action_result,
            "last_reflection": self.last_reflection,
            "candidate_urls": self.candidate_urls.copy(),
            "candidate_index": self.candidate_index,
            "opportunity_evidence": [item.copy() for item in self.opportunity_evidence],
            "selected_opportunity": (
                self.selected_opportunity.copy()
                if self.selected_opportunity
                else None
            ),
            "search_queries": self.search_queries.copy(),
            "research_updated_at": self.research_updated_at,
            "source_history": [item.copy() for item in self.source_history],
            "opportunity_synthesis": [item.copy() for item in self.opportunity_synthesis],
            "validation_plan": self.validation_plan.copy() if self.validation_plan else None,
            "build_decision": self.build_decision.copy() if self.build_decision else None,
            "build_spec": self.build_spec.copy() if self.build_spec else None,
            "build_plan": self.build_plan.copy() if self.build_plan else None,
        }
