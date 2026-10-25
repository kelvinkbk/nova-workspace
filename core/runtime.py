from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.brain import BrainContext, BrainDecision, NovaBrain
from core.result_interpreter import interpret_action_result
from core.opportunity_evaluator import (
    candidate_urls_from_search,
    check_selected_opportunity,
    select_best_opportunity,
    summarize_evidence_comparison,
)
from core.evidence_extractor import extract_opportunity_evidence
from core.opportunity_synthesis import synthesize_opportunity_evidence
from core.search_strategy import next_search_query
from core.validation_planner import build_validation_plan
from core.validation_executor import advance_validation_plan, choose_validation_action
from core.build_decision import decide_first_build
from core.build_spec import build_minimal_spec
from core.build_plan import compile_build_plan
from core.prototype_evaluator import evaluate_prototype
from core.prototype_review import review_prototype
from core.prototype_gate import check_prototype_gate
from core.prototype_failure import diagnose_project_test_failure
from core.prototype_repair import build_repair_plan
from core.prototype_repair_controller import choose_repair_action, validate_repair_write
from core.prototype_history import record_prototype_event
from core.prototype_state import validate_prototype_state
from core.capability_manifest import CapabilityManifest
from core.capability_gate import evaluate_capability
from core.capability_integrity import CapabilityIntegrityLock
from core.prototype_handoff import create_prototype_handoff
from core.experiment_planner import create_next_experiment
from core.experiment_controller import choose_experiment_action, record_experiment_result
from core.experiment_evaluator import evaluate_experiment_result
from core.experiment_followup import create_followup_experiment
from core.experiment_decision import decide_experiment_outcome
from core.real_world_validation_gate import create_real_world_validation_gate
from core.real_world_validation_contract import create_validation_request_spec
from core.real_world_validation_request import build_real_world_validation_request
from core.real_world_validation_request_history import record_real_world_validation_request
from core.real_world_validation_request_integrity import validate_real_world_validation_request_integrity
from core.real_world_validation_approval_binding import (
    validate_real_world_validation_approval_binding,
)
from core.real_world_validation_approval_enforcement import (
    validate_real_world_validation_approval_enforcement,
)
from core.real_world_validation_approval_binding_history import (
    record_real_world_validation_approval_binding,
)
from core.capability_request import create_capability_request
from core.capability_request_controller import store_capability_request
from core.capability_request_history import record_capability_request
from core.capability_approval import record_capability_approval
from database.source_repo import set_source, unseen_urls
from database.memory_repository import (
    load_working_memory,
    save_episode,
    save_journal_entry,
    search_memory as search_memory_records,
    save_working_memory,
)
from memory.episodic import Episode
from memory.journal import JournalEntry
from memory.working import WorkingMemory
from security.policy import PolicyDecision, SecurityPolicy
from tools.builtin import record_observation
from tools.executor import ToolExecutor
from tools.environment import environment_map
from tools.filesystem import list_project_files, read_project_file, PROJECT_ROOT
from tools.memory import memory_search
from tools.network import http_get
from tools.search import web_search
from tools.sandbox import sandbox_run_python, sandbox_write_file
from tools.sandbox_build import build_scaffold
from tools.sandbox_tests import sandbox_run_project_tests
from tools.registry import ToolDefinition, ToolRegistry
from tools.system import system_status
from finance.ledger import finance_status


@dataclass
class RuntimeState:
    status: str = "OFFLINE"
    cycle: int = 0
    started_at: str | None = None
    last_action: str | None = None
    last_reflection: str | None = None
    brain: NovaBrain | None = None
    policy: SecurityPolicy | None = None
    registry: ToolRegistry | None = None
    executor: ToolExecutor | None = None
    capabilities: CapabilityManifest | None = None
    capability_lock: CapabilityIntegrityLock | None = None

    def __post_init__(self) -> None:
        if self.brain is None:
            self.brain = NovaBrain()
        if self.capabilities is None:
            self.capabilities = CapabilityManifest()
        if self.capability_lock is None:
            self.capability_lock = CapabilityIntegrityLock.from_manifest(
                self.capabilities
            )
        if self.policy is None:
            self.policy = SecurityPolicy()
        if self.registry is None:
            self.registry = ToolRegistry()
            self.registry.register(
                ToolDefinition(
                    name="record_observation",
                    description="Record the current observation.",
                    handler=record_observation,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="system_status",
                    description="Read basic system information. Read-only.",
                    handler=system_status,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="finance_status",
                    description="Read NOVA's evidence-based revenue and expense ledger. Read-only; pending items are excluded from verified totals.",
                    handler=finance_status,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="memory_search",
                    description="Search NOVA's stored memories. Read-only.",
                    handler=memory_search,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="environment_map",
                    description="Describe NOVA's currently available capabilities. Read-only.",
                    handler=lambda: environment_map(self.registry, self.capabilities),
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="list_project_files",
                    description="List files inside NOVA's project workspace. Read-only.",
                    handler=list_project_files,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="read_project_file",
                    description="Read a UTF-8 text file inside NOVA's project workspace. Read-only.",
                    handler=read_project_file,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="http_get",
                    description="Fetch a public HTTP/HTTPS resource with GET only. Read-only.",
                    handler=http_get,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="web_search",
                    description="Search the public web and return untrusted search results. Read-only.",
                    handler=web_search,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="sandbox_write",
                    description="Write a text prototype file only inside NOVA's isolated sandbox. No production workspace writes.",
                    handler=sandbox_write_file,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="sandbox_run_python",
                    description="Run one Python prototype inside NOVA's isolated sandbox with a hard timeout and bounded output.",
                    handler=sandbox_run_python,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="sandbox_build",
                    description="Create a non-overwriting prototype scaffold only inside NOVA's isolated sandbox.",
                    handler=build_scaffold,
                )
            )
            self.registry.register(
                ToolDefinition(
                    name="sandbox_run_project_tests",
                    description="Run the generated test_app.py inside a sandbox project with bounded time and output.",
                    handler=sandbox_run_project_tests,
                )
            )
        if self.executor is None:
            self.executor = ToolExecutor(self.registry, self.policy)

    def start(self) -> None:
        self.status = "ONLINE"
        self.started_at = datetime.now(timezone.utc).isoformat()
        memory = load_working_memory()
        if memory.current_goal:
            memory.reset_research_state()
            save_working_memory(memory)

    def observe(self) -> str:
        return f"Runtime status={self.status}, cycle={self.cycle}"

    def build_workspace_context(self) -> str:
        """Build a small, bounded snapshot of NOVA's own project."""
        key_files = [
            "README.md",
            "core/identity.py",
            "core/runtime.py",
            "security/policy.py",
            "tools/registry.py",
        ]

        sections = [
            f"Workspace root: {PROJECT_ROOT}",
            "Key files are provided as bounded read-only context.",
        ]

        for relative_path in key_files:
            try:
                content = read_project_file(relative_path)
            except Exception as exc:  # pragma: no cover - defensive boundary
                content = f"Unable to read file: {exc}"
            if len(content) > 1800:
                content = content[:1800] + "\\n...[truncated]"
            sections.append(f"\\n--- {relative_path} ---\\n{content}")

        return "\\n".join(sections)

    def recall_memory(
        self,
        working_memory: dict | None,
    ) -> list[dict]:
        memory = working_memory or {}
        goal = (memory.get("current_goal") or "").strip()
        task = (memory.get("current_task") or "").strip()
        query = goal or task
        if not query:
            return []
        return search_memory_records(query, limit=5)

    def think(
        self,
        observation: str,
        identity: dict | None = None,
        working_memory: dict | None = None,
        recent_episodes: list[dict] | None = None,
        recent_journal: list[dict] | None = None,
        available_actions: list[str] | None = None,
        external_context: str = "",
    ) -> BrainDecision:
        workspace_context = self.build_workspace_context()
        actions = available_actions or []
        recalled_memories = self.recall_memory(working_memory)
        tool_descriptions = {}
        for action in actions:
            tool = self.registry.get(action)
            if tool is not None:
                tool_descriptions[action] = tool.description
        context = BrainContext(
            identity=identity or {},
            working_memory=working_memory or {},
            observation=observation,
            available_actions=actions,
            workspace_context=workspace_context,
            external_context=external_context,
            tool_descriptions=tool_descriptions,
            recent_episodes=recent_episodes or [],
            recent_journal=recent_journal or [],
            recalled_memories=recalled_memories,
        )
        return self.brain.think(context)

    def authorize(self, decision: BrainDecision) -> PolicyDecision:
        policy_decision = self.policy.evaluate(decision.action)
        if not policy_decision.allowed:
            return policy_decision

        manifest = self.capabilities or CapabilityManifest()
        integrity = (
            self.capability_lock.verify(manifest)
            if self.capability_lock is not None
            else None
        )
        if integrity is not None and not integrity.intact:
            return PolicyDecision(
                action=decision.action,
                allowed=False,
                reason=f"Capability integrity check failed: {integrity.reason}",
            )

        capability_decision = evaluate_capability(
            decision.action,
            manifest,
        )
        if capability_decision.allowed:
            return policy_decision

        return PolicyDecision(
            action=decision.action,
            allowed=False,
            reason=capability_decision.reason,
        )

    @staticmethod
    def _rebuild_working_memory(data: dict | None) -> WorkingMemory:
        state = data or {}
        return WorkingMemory(
            current_goal=state.get("current_goal"),
            current_task=state.get("current_task"),
            active_project=state.get("active_project"),
            notes=list(state.get("notes") or []),
            plan_steps=list(state.get("plan_steps") or []),
            plan_index=int(state.get("plan_index") or 0),
            plan_goal=state.get("plan_goal"),
            last_action=state.get("last_action"),
            last_action_result=state.get("last_action_result"),
            last_reflection=state.get("last_reflection"),
            candidate_urls=list(state.get("candidate_urls") or []),
            candidate_index=int(state.get("candidate_index") or 0),
            opportunity_evidence=[
                dict(item) for item in (state.get("opportunity_evidence") or [])
            ],
            selected_opportunity=(
                dict(state["selected_opportunity"])
                if isinstance(state.get("selected_opportunity"), dict)
                else None
            ),
            search_queries=list(state.get("search_queries") or []),
            research_updated_at=state.get("research_updated_at"),
            source_history=[dict(item) for item in (state.get("source_history") or [])],
            opportunity_synthesis=[dict(item) for item in (state.get("opportunity_synthesis") or [])],
            validation_plan=(
                dict(state["validation_plan"])
                if isinstance(state.get("validation_plan"), dict)
                else None
            ),
            build_decision=(
                dict(state["build_decision"])
                if isinstance(state.get("build_decision"), dict)
                else None
            ),
            build_spec=(
                dict(state["build_spec"])
                if isinstance(state.get("build_spec"), dict)
                else None
            ),
            build_plan=(
                dict(state["build_plan"])
                if isinstance(state.get("build_plan"), dict)
                else None
            ),
        )

    @staticmethod
    def _sanitize_research_state(data: dict | None) -> dict:
        memory = RuntimeState._rebuild_working_memory(data)
        if memory.research_state_stale():
            goal = memory.current_goal
            memory.reset_research_state()
            memory.current_goal = goal
            memory.add_note("Stale opportunity research was discarded; starting a fresh research cycle.")
            save_working_memory(memory)
        return memory.to_dict()

    @staticmethod
    def choose_progress_action(
        current_action: str,
        available_actions: list[str] | None,
        goal: str,
    ) -> str | None:
        actions = available_actions or []
        if not actions:
            return None

        candidates = [
            "web_search",
            "memory_search",
            "environment_map",
            "list_project_files",
            "system_status",
            "record_observation",
        ]
        lowered_goal = (goal or "").lower()

        for action in candidates:
            if action in actions and action != current_action:
                if action == "web_search" and any(
                    word in lowered_goal
                    for word in ("money", "financial", "earning", "income", "business", "self-sustain")
                ):
                    return action
                if action != "web_search":
                    return action

        return next((action for action in actions if action != current_action), None)

    @staticmethod
    def progress_action_input(action: str, goal: str) -> dict:
        if action == "web_search":
            return {"query": goal or "legitimate earning opportunities"}
        if action == "memory_search":
            return {"query": goal or "previous useful experience"}
        return {}

    @classmethod
    def normalize_action_input(
        cls,
        decision: BrainDecision,
        working_memory: dict | None,
    ) -> BrainDecision:
        action = decision.action
        action_input = dict(decision.action_input or {})
        goal = (decision.goal or (working_memory or {}).get("current_goal") or "").strip()

        if action == "web_search" and not str(action_input.get("query", "")).strip():
            previous_queries = (working_memory or {}).get("search_queries") or []
            action_input["query"] = (
                next_search_query(goal, previous_queries)
                if previous_queries
                else (goal or "legitimate earning opportunities")
            )
        elif action == "memory_search" and not str(action_input.get("query", "")).strip():
            action_input["query"] = goal or "previous useful experience"
        elif action == "http_get" and not str(action_input.get("url", "")).strip():
            return decision

        if action_input != decision.action_input:
            return BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                decision.action,
                decision.reason + " Input was normalized from current goal.",
                action_input,
            )
        return decision

    def extract_and_store_evidence(
        self,
        memory: WorkingMemory,
        decision: BrainDecision,
        action_result: str,
    ) -> None:
        if decision.action != "http_get":
            return
        if not action_result.startswith("[BEGIN UNTRUSTED WEB CONTENT]"):
            return
        url = str((decision.action_input or {}).get("url", "")).strip()
        goal = memory.current_goal or decision.goal
        if not url or not goal:
            return
        if action_result.startswith(("Network request failed:", "Network denied:")):
            set_source(url, goal, "failed", action_result[:300])
            return
        evidence = extract_opportunity_evidence(
            action_result,
            url,
            title="",
            goal=memory.current_goal or decision.goal,
        ).to_dict()
        if evidence.get("content_relevance") == "low":
            note = f"Rejected low-relevance source: {url}"
            if note not in memory.notes:
                memory.add_note(note)
            set_source(url, goal, "rejected", note)
            return
        set_source(url, goal, "useful", "accepted as relevant opportunity evidence")
        memory.opportunity_evidence = [
            item for item in memory.opportunity_evidence
            if item.get("url") != url
        ]
        memory.opportunity_evidence.append(evidence)

    def update_candidate_queue(
        self,
        memory: WorkingMemory,
        decision: BrainDecision,
        action_result: str,
    ) -> None:
        if decision.action == "web_search":
            memory.touch_research_state()
            memory.selected_opportunity = None
            query = str((decision.action_input or {}).get("query") or "").strip()
            if query and query not in memory.search_queries:
                memory.search_queries.append(query)
            candidates = candidate_urls_from_search(
                action_result,
                memory.current_goal or decision.goal,
            )
            candidates = unseen_urls(candidates, memory.current_goal or decision.goal)
            if candidates:
                memory.candidate_urls = candidates
                memory.candidate_index = 0
                memory.current_task = (
                    f"Inspect ranked opportunity candidate 1 of {len(candidates)}"
                )
            return

        if decision.action == "http_get":
            memory.touch_research_state()
        if decision.action == "http_get" and memory.candidate_urls:
            if memory.candidate_index < len(memory.candidate_urls):
                memory.candidate_index += 1
            if memory.candidate_index < len(memory.candidate_urls):
                memory.current_task = (
                    f"Inspect ranked opportunity candidate "
                    f"{memory.candidate_index + 1} of {len(memory.candidate_urls)}"
                )
            else:
                memory.current_task = "Compare the inspected opportunity candidates"

    def update_adaptive_plan(
        self,
        working_memory: dict | None,
        decision: BrainDecision,
        policy_decision: PolicyDecision,
        action_result: str,
        available_actions: list[str] | None = None,
    ) -> WorkingMemory:
        memory = self._rebuild_working_memory(working_memory)

        if memory.current_goal != decision.goal:
            memory.current_goal = decision.goal
            memory.set_plan(decision.plan, decision.goal)
        elif not memory.plan_steps:
            memory.set_plan(decision.plan, decision.goal)

        successful = (
            policy_decision.allowed
            and not action_result.startswith((
                "Action denied:",
                "Network request failed:",
                "Network denied:",
                "Search failed:",
                "File read failed:",
                "File not found:",
            ))
        )

        if successful and memory.has_active_plan():
            memory.advance_plan()

        self.extract_and_store_evidence(memory, decision, action_result)
        memory.opportunity_synthesis = [
            item.to_dict()
            for item in synthesize_opportunity_evidence(memory.opportunity_evidence)
        ]

        if (
            isinstance(memory.build_plan, dict)
            and memory.build_plan.get("status") == "sandbox_complete"
            and isinstance(memory.build_plan.get("followup_experiment"), dict)
            and memory.build_plan["followup_experiment"].get("status") == "ready"
            and decision.action == "web_search"
        ):
            followup_result = record_experiment_result(
                memory.build_plan["followup_experiment"],
                decision.action,
                action_result,
            )
            evaluation = evaluate_experiment_result(action_result)
            followup_result["evaluation"] = evaluation.to_dict()
            if evaluation.status == "blocked":
                followup_result["status"] = "blocked"
            memory.build_plan["followup_experiment"] = followup_result
            memory.build_plan["followup_count"] = int(
                memory.build_plan.get("followup_count") or 0
            ) + 1
            experiment_decision = decide_experiment_outcome(
                memory.build_plan.get("next_experiment"),
                followup_result,
            )
            memory.build_plan["experiment_decision"] = experiment_decision.to_dict()
            validation_gate = create_real_world_validation_gate(
                experiment_decision.to_dict(),
                available_actions or [],
            )
            memory.build_plan["real_world_validation_gate"] = validation_gate.to_dict()
            validation_request = create_validation_request_spec(
                experiment_decision.to_dict(),
                self.capabilities or CapabilityManifest(),
            )
            memory.build_plan["real_world_validation_request"] = validation_request.to_dict()
            validation_request_packet = build_real_world_validation_request(
                validation_request.to_dict()
            )
            memory.build_plan["real_world_validation_request_packet"] = (
                validation_request_packet.to_dict()
            )
            capability_request = create_capability_request(
                tuple(validation_request.required_capabilities),
                self.capabilities or CapabilityManifest(),
            )
            capability_request_dict = capability_request.to_dict()
            validation_request_integrity = validate_real_world_validation_request_integrity(
                validation_request_packet.to_dict(), capability_request_dict
            )
            memory.build_plan["real_world_validation_request_integrity"] = validation_request_integrity
            record_real_world_validation_request(
                memory.build_plan,
                validation_request_packet.to_dict(),
                integrity=validation_request_integrity,
            )
            if not validation_request_integrity["valid"]:
                memory.build_plan["real_world_validation_request_packet"]["status"] = "blocked"
                memory.build_plan["real_world_validation_request_packet"]["action"] = None
                memory.build_plan["real_world_validation_request_packet"]["side_effects_allowed"] = False
                memory.build_plan["real_world_validation_request_packet"]["execution_status"] = "not_executed"
            store_capability_request(memory.build_plan, capability_request_dict)
            record_capability_request(memory.build_plan, capability_request_dict)
            validation_approval_binding = validate_real_world_validation_approval_binding(
                memory.build_plan["real_world_validation_request_packet"],
                capability_request_dict,
                memory.build_plan.get("capability_approval"),
            )
            memory.build_plan["real_world_validation_approval_binding"] = (
                validation_approval_binding
            )
            if not validation_approval_binding["valid"]:
                packet = memory.build_plan["real_world_validation_request_packet"]
                packet["status"] = "blocked"
                packet["action"] = None
                packet["side_effects_allowed"] = False
                packet["execution_status"] = "not_executed"
                enforcement = {
                    "status": "blocked",
                    "reason": "Validation approval binding failed; execution remains disabled.",
                    "issues": list(validation_approval_binding["issues"]),
                }
            else:
                enforcement = {
                    "status": "validated",
                    "reason": "Validation approval binding passed; activation remains disabled.",
                    "issues": [],
                }
            enforcement_check = validate_real_world_validation_approval_enforcement(
                validation_approval_binding,
                enforcement,
                memory.build_plan["real_world_validation_request_packet"],
            )
            if not enforcement_check["valid"]:
                packet = memory.build_plan["real_world_validation_request_packet"]
                packet["status"] = "blocked"
                packet["action"] = None
                packet["side_effects_allowed"] = False
                packet["execution_status"] = "not_executed"
                enforcement = {
                    "status": "blocked",
                    "reason": "Validation approval enforcement consistency failed; execution remains disabled.",
                    "issues": list(enforcement_check["issues"]),
                }
            validation_approval_binding["enforcement_status"] = enforcement["status"]
            validation_approval_binding["enforcement_reason"] = enforcement["reason"]
            memory.build_plan["real_world_validation_approval_binding_enforcement"] = enforcement
            record_real_world_validation_approval_binding(
                memory.build_plan,
                validation_approval_binding,
            )
            record_prototype_event(
                memory.build_plan,
                "followup_experiment",
                evaluation.status,
                action_result,
            )
            memory.current_task = validation_gate.next_action
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        if (
            isinstance(memory.build_plan, dict)
            and memory.build_plan.get("status") == "sandbox_complete"
            and isinstance(memory.build_plan.get("next_experiment"), dict)
            and decision.action == "web_search"
        ):
            experiment_result = record_experiment_result(
                memory.build_plan["next_experiment"],
                decision.action,
                action_result,
            )
            evaluation = evaluate_experiment_result(action_result)
            experiment_result["evaluation"] = evaluation.to_dict()
            if evaluation.status == "blocked":
                experiment_result["status"] = "blocked"
            memory.build_plan["next_experiment"] = experiment_result
            followup = create_followup_experiment(
                experiment_result,
                evaluation.to_dict(),
                int(memory.build_plan.get("followup_count") or 0),
            )
            if followup is not None:
                memory.build_plan["followup_experiment"] = followup.to_dict()
            record_prototype_event(
                memory.build_plan,
                "next_experiment",
                evaluation.status,
                action_result,
            )
            memory.current_task = (
                "Next bounded experiment produced evidence; interpret it conservatively before defining another experiment."
                if evaluation.status == "evidence_found"
                else "Next bounded experiment is inconclusive; do not claim demand or modify the frozen prototype."
                if evaluation.status == "inconclusive"
                else "Next bounded experiment failed; preserve the frozen prototype and reassess."
            )
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        if (
            decision.action == "sandbox_build"
            and isinstance(memory.build_plan, dict)
            and action_result.startswith("Sandbox scaffold created:")
        ):
            memory.build_plan["status"] = "scaffolded"
            record_prototype_event(
                memory.build_plan,
                "scaffold",
                "created",
                action_result,
            )
            marker = "Sandbox scaffold created: "
            memory.build_plan["scaffold_path"] = (
                action_result.split(marker, 1)[1].split(" with", 1)[0].strip().rstrip("/")
            )
            memory.current_task = (
                "Review the sandbox scaffold, then run its prototype tests."
            )
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        if (
            decision.action == "sandbox_write"
            and isinstance(memory.build_plan, dict)
            and memory.build_plan.get("status") == "test_failed"
        ):
            memory.build_plan["repair_controller"] = choose_repair_action(
                memory.build_plan
            ).to_dict()
            if action_result.startswith("Sandbox file written:"):
                memory.build_plan["repair_attempts"] = int(
                    memory.build_plan.get("repair_attempts") or 0
                ) + 1
                memory.build_plan["status"] = "repair_applied"
                memory.build_plan["repair_result"] = action_result[:1200]
                record_prototype_event(
                    memory.build_plan,
                    "repair",
                    "applied",
                    action_result,
                )
                memory.current_task = (
                    "Bounded prototype repair applied; rerun the smoke test before project tests."
                )
            else:
                memory.build_plan["repair_result"] = action_result[:1200]
                record_prototype_event(
                    memory.build_plan,
                    "repair",
                    "not_applied",
                    action_result,
                )
                memory.current_task = (
                    "Repair was not applied; do not exceed the bounded repair attempt."
                )
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        if (
            decision.action == "sandbox_run_python"
            and isinstance(memory.build_plan, dict)
        ):
            if action_result.startswith("Sandbox execution passed"):
                memory.build_plan["status"] = "tested"
                memory.build_plan["prototype_result"] = action_result[:1200]
                record_prototype_event(
                    memory.build_plan,
                    "smoke_test",
                    "passed",
                    action_result,
                )
                memory.current_task = (
                    "Prototype smoke test passed; run the generated project tests."
                )
            elif action_result.startswith("Sandbox execution failed"):
                memory.build_plan["status"] = "test_failed"
                memory.build_plan["prototype_result"] = action_result[:1200]
                record_prototype_event(
                    memory.build_plan,
                    "smoke_test",
                    "failed",
                    action_result,
                )
                memory.current_task = (
                    "Prototype smoke test failed; diagnose the sandbox prototype before proceeding."
                )
            else:
                memory.build_plan["prototype_result"] = action_result[:1200]
                memory.current_task = (
                    "Prototype test did not complete successfully; inspect the sandbox result."
                )
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        if (
            decision.action == "sandbox_run_project_tests"
            and isinstance(memory.build_plan, dict)
        ):
            memory.build_plan["project_test_result"] = action_result[:1200]
            if action_result.startswith("Sandbox project tests passed"):
                record_prototype_event(
                    memory.build_plan,
                    "project_tests",
                    "passed",
                    action_result,
                )
                evaluation = evaluate_prototype(
                    memory.build_plan,
                    smoke_result=str(memory.build_plan.get("prototype_result") or ""),
                    project_test_result=action_result,
                )
                memory.build_plan["prototype_evaluation"] = evaluation.to_dict()
                memory.build_plan["status"] = evaluation.status
                if evaluation.status == "verified":
                    review = review_prototype(memory.build_plan)
                    memory.build_plan["prototype_review"] = review.to_dict()
                    memory.build_plan["status"] = review.status
                    if review.status == "reviewed":
                        gate = check_prototype_gate(memory.build_plan)
                        memory.build_plan["prototype_gate"] = gate.to_dict()
                        if gate.status == "sandbox_complete":
                            memory.build_plan["status"] = "sandbox_complete"
                            handoff = create_prototype_handoff(memory.build_plan)
                            if handoff is not None:
                                memory.build_plan["prototype_handoff"] = handoff.to_dict()
                                experiment = create_next_experiment(memory.build_plan)
                                if experiment is not None:
                                    memory.build_plan["next_experiment"] = experiment.to_dict()
                                    memory.current_task = experiment.scope[0]
                                else:
                                    memory.current_task = handoff.next_action
                            else:
                                memory.current_task = gate.next_action
                        else:
                            memory.build_plan["status"] = "review_required"
                            memory.current_task = gate.next_action
                    else:
                        memory.build_plan["prototype_gate"] = check_prototype_gate(
                            memory.build_plan
                        ).to_dict()
                        memory.current_task = (
                            "Prototype structural review found blockers; resolve them before proceeding."
                        )
                else:
                    memory.current_task = (
                        "Prototype needs review; resolve the deterministic acceptance blockers."
                    )
            elif action_result.startswith("Sandbox project tests failed"):
                memory.build_plan["status"] = "test_failed"
                record_prototype_event(
                    memory.build_plan,
                    "project_tests",
                    "failed",
                    action_result,
                )
                memory.build_plan["prototype_evaluation"] = evaluate_prototype(
                    memory.build_plan,
                    smoke_result=str(memory.build_plan.get("prototype_result") or ""),
                    project_test_result=action_result,
                ).to_dict()
                failure = diagnose_project_test_failure(action_result)
                memory.build_plan["prototype_failure"] = failure.to_dict()
                repair_plan = build_repair_plan(failure.to_dict())
                memory.build_plan["prototype_repair_plan"] = repair_plan.to_dict()
                memory.current_task = (
                    f"Project tests failed ({failure.failure_type}); use the bounded repair plan "
                    "to diagnose before any prototype modification."
                )
            else:
                memory.current_task = (
                    "Project tests did not complete successfully; inspect the sandbox result."
                )
            memory.last_action = decision.action
            memory.last_action_result = action_result
            memory.last_reflection = self.last_reflection
            save_working_memory(memory)
            return memory

        build_active = (
            isinstance(memory.build_plan, dict)
            and memory.build_plan.get("status", "ready") == "ready"
            and isinstance(memory.build_decision, dict)
            and memory.build_decision.get("status") == "build_minimal"
        )
        validation_active = (
            isinstance(memory.validation_plan, dict)
            and isinstance(memory.selected_opportunity, dict)
            and memory.selected_opportunity.get("validation", {}).get("status") == "validated"
        )
        if build_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_build",
                "Build decision is approved; create the smallest prototype scaffold inside the isolated sandbox.",
                {"build_plan": memory.build_plan},
            )
        elif validation_active:
            memory.validation_plan = advance_validation_plan(
                memory.validation_plan,
                decision.action,
                action_result,
            )
            control = choose_validation_action(memory.validation_plan)
            if control.status == "blocked":
                memory.validation_plan["status"] = "blocked"
                memory.validation_plan["blocker"] = control.reason
                memory.build_decision = decide_first_build(
                    memory.selected_opportunity,
                    memory.validation_plan,
                    memory.opportunity_evidence,
                ).to_dict()
                if memory.build_decision["status"] == "build_minimal":
                    memory.build_spec = build_minimal_spec(
                        memory.build_decision,
                        memory.validation_plan,
                        memory.opportunity_evidence,
                    )
                    memory.build_spec = (
                        memory.build_spec.to_dict()
                        if memory.build_spec is not None
                        else None
                    )
                    memory.build_plan = (
                        compile_build_plan(memory.build_spec).to_dict()
                        if memory.build_spec is not None
                        else None
                    )
                    memory.current_task = (
                        "Review the smallest build plan before implementation."
                    )
                else:
                    memory.current_task = (
                        "Gather the missing evidence before making a build decision."
                    )
            else:
                memory.build_decision = None
                memory.build_spec = None
                memory.build_plan = None
                memory.current_task = (
                    f"Execute validation step {control.step_index + 1}: "
                    f"{memory.validation_plan.get('steps', [])[control.step_index]}"
                )
        else:
            self.update_candidate_queue(memory, decision, action_result)

            if (
                decision.action == "http_get"
                and memory.candidate_urls
                and memory.candidate_index >= len(memory.candidate_urls)
                and len(memory.opportunity_evidence) >= 2
            ):
                comparison = summarize_evidence_comparison(
                    memory.opportunity_evidence,
                    memory.current_goal or decision.goal,
                )
                if comparison not in memory.notes:
                    memory.add_note(comparison)
                selection = select_best_opportunity(
                    memory.opportunity_evidence,
                    memory.current_goal or decision.goal,
                )
                memory.selected_opportunity = {
                    "status": selection.status,
                    "title": selection.title,
                    "url": selection.url,
                    "score": selection.score,
                    "reasons": list(selection.reasons),
                    "evidence_count": selection.evidence_count,
                }
                if selection.status == "selected":
                    validation = check_selected_opportunity(
                        memory.selected_opportunity,
                        memory.opportunity_evidence,
                    )
                    memory.selected_opportunity["validation"] = validation.to_dict() if hasattr(validation, "to_dict") else {
                        "status": validation.status,
                        "title": validation.title,
                        "url": validation.url,
                        "reasons": list(validation.reasons),
                        "required_signals": list(validation.required_signals),
                        "evidence_count": validation.evidence_count,
                    }
                    if validation.status == "validated":
                        plan = build_validation_plan(
                            memory.selected_opportunity,
                            memory.opportunity_evidence,
                        )
                        memory.validation_plan = plan.to_dict() if plan is not None else None
                        memory.build_decision = None
                        memory.current_task = f"Execute the zero-cost validation plan for: {selection.title}"
                    else:
                        memory.validation_plan = None
                        memory.build_decision = None
                        memory.build_spec = None
                        memory.current_task = "Find more evidence for the selected opportunity"
                else:
                    memory.validation_plan = None
                    memory.build_decision = None
                    memory.build_spec = None
                    memory.build_plan = None
                    memory.current_task = "Find and inspect more opportunity evidence"

        memory.last_action = decision.action
        memory.last_action_result = action_result
        memory.last_reflection = self.last_reflection
        save_working_memory(memory)
        return memory

    def act(
        self,
        decision: BrainDecision,
        policy_decision: PolicyDecision,
    ) -> str:
        if not policy_decision.allowed:
            return self.executor.execute(
                decision.action,
                decision.action_input,
            )
        self.last_action = decision.action
        return self.executor.execute(
            decision.action,
            decision.action_input,
        )

    def reflect(self, decision: BrainDecision, action_result: str, policy_decision: PolicyDecision) -> str:
        if not policy_decision.allowed:
            outcome = "blocked"
            next_step = "Choose an action permitted by the security policy."
        elif action_result.startswith("Action denied:"):
            outcome = "failed"
            next_step = "Inspect the tool input and retry only with valid input."
        elif action_result.startswith(("Network request failed:", "Network denied:", "Search failed:")):
            outcome = "failed"
            next_step = "Try a different read-only source or revise the request."
        elif action_result.startswith(("File read failed:", "File not found:")):
            outcome = "failed"
            next_step = "Choose an existing readable project file."
        else:
            outcome = "completed"
            next_step = "Use this result as evidence for the next decision."

        actual = action_result if len(action_result) <= 500 else action_result[:500] + "...[truncated]"
        self.last_reflection = (
            f"Cycle {self.cycle} reflection: decision={decision.action}; "
            f"expected={decision.reason}; actual={actual}; "
            f"outcome={outcome}; next_step={next_step}"
        )
        return self.last_reflection

    def persist_cycle(
        self,
        observation: str,
        decision: BrainDecision,
        policy_decision: PolicyDecision,
        action_result: str,
        reflection: str,
        life_day: int,
    ) -> None:
        episode = Episode(
            event="NOVA cognitive cycle executed",
            context=(
                f"Observation: {observation}\n"
                f"Thought: {decision.thought}\n"
                f"Goal: {decision.goal}\n"
                f"Plan: {decision.plan}\n"
                f"Decision: {decision.action}\n"
                f"Policy allowed: {policy_decision.allowed}\n"
                f"Policy reason: {policy_decision.reason}"
            ),
            outcome=(
                f"Action: {action_result}\n"
                f"Reflection: {reflection}"
            ),
            importance=3,
        )
        save_episode(episode)
        journal_entry = JournalEntry(
            title=f"Cognitive cycle {self.cycle}",
            content=(
                f"Thought: {decision.thought}\n"
                f"Goal: {decision.goal}\n"
                f"Decision: {decision.action}\n"
                f"Policy: {policy_decision.allowed} ({policy_decision.reason})\n"
                f"Action: {action_result}\n"
                f"Reflection: {reflection}"
            ),
            life_day=life_day,
        )
        save_journal_entry(journal_entry)

    def run_cycle(
        self,
        life_day: int = 1,
        identity: dict | None = None,
        working_memory: dict | None = None,
        recent_episodes: list[dict] | None = None,
        recent_journal: list[dict] | None = None,
        available_actions: list[str] | None = None,
        external_context: str = "",
    ) -> dict:
        if self.status != "ONLINE":
            raise RuntimeError("NOVA runtime is not online.")
        self.cycle += 1
        working_memory = self._sanitize_research_state(working_memory)
        observation = self.observe()
        decision = self.think(
            observation=observation,
            identity=identity,
            working_memory=working_memory,
            recent_episodes=recent_episodes,
            recent_journal=recent_journal,
            available_actions=available_actions,
            external_context=external_context,
        )
        state = working_memory or {}
        prototype_plan = state.get("build_plan")
        prototype_state = validate_prototype_state(prototype_plan)
        if (
            isinstance(prototype_plan, dict)
            and not prototype_state.valid
        ):
            prototype_plan["prototype_state_validation"] = prototype_state.to_dict()
            prototype_plan["status"] = "review_required"
            state["build_plan"] = prototype_plan
            save_working_memory(self._rebuild_working_memory(state))
        experiment_plan = (
            state.get("build_plan", {}).get("next_experiment")
            if isinstance(state.get("build_plan"), dict)
            else None
        )
        followup_plan = (
            state.get("build_plan", {}).get("followup_experiment")
            if isinstance(state.get("build_plan"), dict)
            else None
        )
        followup_control = choose_experiment_action(
            (
                {
                    "status": followup_plan.get("status"),
                    "title": followup_plan.get("title"),
                    "hypothesis": followup_plan.get("purpose"),
                }
                if isinstance(followup_plan, dict)
                else None
            ),
            available_actions,
        )
        experiment_control = choose_experiment_action(
            experiment_plan,
            available_actions,
        )
        followup_active = followup_control.status == "ready"
        experiment_active = (
            not followup_active
            and experiment_control.status == "ready"
        )
        validation_control = choose_validation_action(state.get("validation_plan"))
        validation_active = validation_control.status in {"ready", "blocked"}
        build_active = (
            isinstance(state.get("build_plan"), dict)
            and state["build_plan"].get("status", "ready") == "ready"
            and isinstance(state.get("build_decision"), dict)
            and state["build_decision"].get("status") == "build_minimal"
        )
        prototype_test_active = (
            isinstance(state.get("build_plan"), dict)
            and state["build_plan"].get("status") == "scaffolded"
            and bool(state["build_plan"].get("scaffold_path"))
        )
        project_test_active = (
            isinstance(state.get("build_plan"), dict)
            and state["build_plan"].get("status") == "tested"
            and bool(state["build_plan"].get("scaffold_path"))
        )
        repair_verify_active = (
            isinstance(state.get("build_plan"), dict)
            and state["build_plan"].get("status") == "repair_applied"
            and bool(state["build_plan"].get("scaffold_path"))
        )
        repair_control = choose_repair_action(state.get("build_plan"))
        repair_active = (
            isinstance(state.get("build_plan"), dict)
            and state["build_plan"].get("status") == "test_failed"
            and repair_control.status == "ready"
            and "sandbox_write" in (available_actions or [])
        )

        previous_action = state.get("last_action")
        previous_result = state.get("last_action_result") or ""
        interpretation = (
            interpret_action_result(
                previous_action,
                previous_result,
                state.get("current_goal") or decision.goal,
            )
            if previous_action and previous_result
            else None
        )

        if followup_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                followup_control.action or "record_observation",
                followup_control.reason,
                followup_control.action_input,
            )
        elif experiment_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                experiment_control.action or "record_observation",
                experiment_control.reason,
                experiment_control.action_input,
            )
        elif repair_verify_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_run_python",
                "A bounded repair was applied; verify the repaired prototype with the smoke test before any further action.",
                {
                    "path": f"{state['build_plan']['scaffold_path']}/app.py",
                    "timeout_seconds": 5,
                },
            )
        elif repair_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_write",
                repair_control.reason,
                decision.action_input,
            )
        elif build_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_build",
                "Build decision is approved; create the smallest prototype scaffold inside the isolated sandbox.",
                {"build_plan": state["build_plan"]},
            )
        elif prototype_test_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_run_python",
                "Prototype scaffold exists; run its bounded smoke test inside the sandbox.",
                {
                    "path": f"{state['build_plan']['scaffold_path']}/app.py",
                    "timeout_seconds": 5,
                },
            )
        elif project_test_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "sandbox_run_project_tests",
                "Prototype smoke test passed; run the generated project test suite inside the sandbox.",
                {
                    "project_path": state["build_plan"]["scaffold_path"],
                    "timeout_seconds": 5,
                },
            )
        elif validation_active:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                validation_control.action or "record_observation",
                validation_control.reason,
                validation_control.action_input,
            )
        else:
            queue = list(state.get("candidate_urls") or [])
            queue_index = int(state.get("candidate_index") or 0)
            next_candidate = (
                queue[queue_index]
                if queue_index < len(queue)
                else None
            )
            if previous_action == "web_search" and previous_result and (
                previous_result.startswith("No search results found")
                or previous_result.startswith("Search failed:")
                or "weak for inspection" in (interpretation.summary if interpretation else "")
            ):
                search_query = next_search_query(
                    state.get("current_goal") or decision.goal,
                    state.get("search_queries") or [],
                )
                decision = BrainDecision(
                    decision.thought,
                    decision.goal,
                    decision.plan,
                    "web_search",
                    "Search strategy selected a new evidence-oriented query after weak or failed results.",
                    {"query": search_query},
                )
            elif previous_action == "http_get" and next_candidate:
                decision = BrainDecision(
                    decision.thought,
                    decision.goal,
                    decision.plan,
                    "http_get",
                    (
                        f"Candidate queue continuation: inspect ranked candidate "
                        f"{queue_index + 1} of {len(queue)}."
                    ),
                    {"url": next_candidate},
                )
            elif interpretation and interpretation.suggested_action:
                suggested = interpretation.suggested_action
                allowed_suggestion = (
                    available_actions is None
                    or suggested in available_actions
                )
                if allowed_suggestion:
                    decision = BrainDecision(
                        decision.thought,
                        decision.goal,
                        decision.plan,
                        suggested,
                        interpretation.summary,
                        interpretation.suggested_input or {},
                    )
        stagnation_detected = False
        if (
            previous_action
            and previous_result
            and decision.action == previous_action
            and (interpretation is None or not interpretation.suggested_action)
            and available_actions
        ):
            next_action = self.choose_progress_action(
                decision.action,
                available_actions,
                decision.goal,
            )
            if next_action:
                stagnation_detected = True
                decision = BrainDecision(
                    decision.thought,
                    decision.goal,
                    decision.plan,
                    next_action,
                    "Progress controller changed the repeated action to avoid stagnation.",
                    self.progress_action_input(next_action, decision.goal),
                )
        elif available_actions and decision.action not in available_actions:
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                available_actions[0],
                "Selected the first currently available action.",
                {},
            )
        decision = self.normalize_action_input(decision, working_memory)
        completed_plan = state.get("build_plan")
        if (
            isinstance(completed_plan, dict)
            and completed_plan.get("status") == "sandbox_complete"
            and decision.action in {
                "sandbox_write",
                "sandbox_build",
            }
        ):
            decision = BrainDecision(
                decision.thought,
                decision.goal,
                decision.plan,
                "record_observation",
                "Prototype is complete; mutation actions are frozen by the completion gate.",
                {},
            )
        if (
            repair_active
            and decision.action == "sandbox_write"
            and isinstance(state.get("build_plan"), dict)
        ):
            repair_input, repair_error = validate_repair_write(
                state["build_plan"],
                decision.action_input,
            )
            if repair_error:
                decision = BrainDecision(
                    decision.thought,
                    decision.goal,
                    decision.plan,
                    "sandbox_write",
                    f"{repair_control.reason} Repair input rejected: {repair_error}.",
                    {},
                )
            else:
                decision = BrainDecision(
                    decision.thought,
                    decision.goal,
                    decision.plan,
                    "sandbox_write",
                    decision.reason,
                    repair_input or {},
                )
        policy_decision = self.authorize(decision)
        action_result = self.act(decision, policy_decision)
        reflection = self.reflect(decision, action_result, policy_decision)
        updated_memory = self.update_adaptive_plan(
            working_memory,
            decision,
            policy_decision,
            action_result,
            available_actions=available_actions,
        )
        self.persist_cycle(
            observation=observation,
            decision=decision,
            policy_decision=policy_decision,
            action_result=action_result,
            reflection=reflection,
            life_day=life_day,
        )
        return {
            "cycle": self.cycle,
            "observation": observation,
            "thought": decision.thought,
            "goal": decision.goal,
            "plan": decision.plan,
            "decision": decision.action,
            "policy_allowed": policy_decision.allowed,
            "policy_reason": policy_decision.reason,
            "action": action_result,
            "reflection": reflection,
            "current_task": updated_memory.current_task,
            "plan_steps": updated_memory.plan_steps,
            "plan_index": updated_memory.plan_index,
            "stagnation_detected": stagnation_detected,
            "build_decision": updated_memory.build_decision,
            "build_spec": updated_memory.build_spec,
            "build_plan": updated_memory.build_plan,
        }

    def stop(self) -> None:
        self.status = "OFFLINE"
