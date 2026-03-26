from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context_builder import ContextBuilder, build_context_builder
from .llm_router import LLMRouter, build_llm_router
from .prompt_manager import PromptManager, build_prompt_manager


@dataclass(slots=True)
class WorkflowResult:
    name: str
    status: str
    steps: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class GTMOrchestrator:
    llm_router: LLMRouter = field(default_factory=build_llm_router)
    context_builder: ContextBuilder = field(default_factory=build_context_builder)
    prompt_manager: PromptManager = field(default_factory=build_prompt_manager)

    async def run_workflow(self, workflow_name: str, payload: dict[str, Any]) -> WorkflowResult:
        steps: list[dict[str, Any]] = [{"step": "received", "payload_keys": sorted(payload.keys())}]
        if workflow_name == "icp_scoring":
            context = self.context_builder.build_profile_text(payload)
            response = await self.llm_router.complete(
                system=self.prompt_manager.load("icp_scoring"),
                user=context,
                format="json",
                metadata={"org_id": payload.get("org_id", "unknown"), "agent_name": "icp_agent"},
            )
            steps.append({"step": "scored", "response": response.content})
        elif workflow_name == "outbound_generation":
            context = self.context_builder.build_full_outbound_context(
                contact=payload.get("contact", {}),
                campaign=payload.get("campaign", {}),
                enrichment=payload.get("enrichment"),
                extra_signals=payload.get("signals"),
            )
            response = await self.llm_router.complete(
                system=self.prompt_manager.load("outbound_personalization"),
                user=context,
                format="json",
                metadata={"org_id": payload.get("org_id", "unknown"), "agent_name": "outbound_agent"},
            )
            steps.append({"step": "generated", "response": response.content})
        else:
            steps.append({"step": "noop", "workflow": workflow_name})
        return WorkflowResult(name=workflow_name, status="completed", steps=steps)
def build_orchestrator() -> GTMOrchestrator:
    return GTMOrchestrator()
