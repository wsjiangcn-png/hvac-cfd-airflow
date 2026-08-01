"""Wire a single Agent with the hello skill bundle."""
from __future__ import annotations

import json
from pathlib import Path

from agent_skill_framework import (
    Agent,
    BundleLoader,
    KnowledgeSkillStore,
    Plan,
    SkillRegistry,
    create_llm,
)

APP_ROOT = Path(__file__).resolve().parent
HELLO = APP_ROOT / "skills" / "hello"


def _offline_compile(plan: Plan, catalog_prompt: str) -> str:
    # Deterministic fallback when LLM is offline or invents names
    name = "friend"
    text = f"{(plan.goal or '')} {' '.join(plan.intents or [])}"
    for token in text.replace(",", " ").split():
        if token.lower() not in {"say", "hello", "to", "a", "the", "please", "greet"}:
            if token[:1].isalpha():
                name = token.strip(".,!")
                break
    return json.dumps({
        "steps": [{
            "id": "s1",
            "skill": "hello_pipeline",
            "input": {"name": name},
            "depends_on": [],
        }]
    })


def build_system() -> tuple[Agent, str]:
    registry = SkillRegistry()
    knowledge = KnowledgeSkillStore()
    loader = BundleLoader(registry, knowledge)
    loader.load_bundle(str(HELLO))

    status_parts = [f"skills={sorted(registry.names())}"]

    llm = None
    try:
        candidate = create_llm()
        if candidate.available():
            llm = candidate
            status_parts.append(f"llm={llm.provider}/{llm.model}")
        else:
            status_parts.append("llm=configured-but-unreachable")
    except Exception as exc:
        status_parts.append(f"llm=off ({exc})")

    def compile_with_fallback(plan: Plan, catalog_prompt: str) -> str:
        if llm is None:
            return _offline_compile(plan, catalog_prompt)
        try:
            data = llm.compile_plan(
                plan.goal,
                plan.intents,
                catalog_prompt,
                skill_schemas={s.name: (s.input_schema or {}) for s in loader.catalog},
            )
            if isinstance(data, dict) and data.get("steps"):
                return json.dumps(data)
        except Exception:
            pass
        return _offline_compile(plan, catalog_prompt)

    agent = Agent(
        registry=registry,
        catalog=loader.catalog,
        name="hello_desk",
        description="greets users and runs the hello pipeline",
        llm=llm,
        compile_llm_call=compile_with_fallback,
        knowledge_store=knowledge,
        knowledge_trigger="soft",
    )
    return agent, " | ".join(status_parts)
