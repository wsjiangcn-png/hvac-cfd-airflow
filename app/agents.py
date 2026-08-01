"""Engineering desk + CFD specialist for HVAC airflow optimization."""
from __future__ import annotations

import json
from pathlib import Path

from agent_skill_framework import (
    Agent,
    AgentRegistry,
    BundleLoader,
    KnowledgeSkillStore,
    Plan,
    SkillRegistry,
    create_llm,
    sanitize_workflow_dict,
)

from app.skill_aliases import SKILL_ALIASES

APP_ROOT = Path(__file__).resolve().parent
HVAC = APP_ROOT / "skills" / "hvac_cfd"


def _wants_optimize(text: str) -> bool:
    t = text.lower()
    keys = ("optim", "damper", "balance", "reduce pressure", "improve comfort", "uniform")
    return any(k in t for k in keys)


def _offline_compile(plan: Plan, catalog_prompt: str) -> str:
    """Deterministic workflow when LLM is offline."""
    text = f"{(plan.goal or '')} {' '.join(plan.intents or [])}"
    skill = (
        "hvac_optimize_dampers_pipeline"
        if _wants_optimize(text)
        else "hvac_airflow_pipeline"
    )
    return json.dumps({
        "steps": [{
            "id": "s1",
            "skill": skill,
            "input": {
                "case_name": "commercial_hvac",
                "inlet_mass_flow_kg_s": 2.5,
                "outlet_pressure_Pa": 0.0,
                "max_delta_p_Pa": 150.0,
                "min_uniformity": 0.75,
            },
            "depends_on": [],
        }]
    })


def build_system() -> tuple[Agent, str]:
    registry = SkillRegistry()
    knowledge = KnowledgeSkillStore()
    loader = BundleLoader(registry, knowledge)
    loader.load_bundle(str(HVAC))

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

    schemas = {s.name: (s.input_schema or {}) for s in loader.catalog}

    def compile_with_fallback(plan: Plan, catalog_prompt: str) -> str:
        if llm is None:
            return _offline_compile(plan, catalog_prompt)
        try:
            data = llm.compile_plan(
                plan.goal,
                plan.intents,
                catalog_prompt,
                skill_schemas=schemas,
                aliases=SKILL_ALIASES,
            )
            if isinstance(data, dict) and data.get("steps"):
                data = sanitize_workflow_dict(
                    data,
                    skill_schemas=schemas,
                    known_skills=set(registry.names()),
                    aliases=SKILL_ALIASES,
                )
                if data.get("steps"):
                    return json.dumps(data)
        except TypeError:
            # Older compile_plan without aliases=
            try:
                data = llm.compile_plan(
                    plan.goal,
                    plan.intents,
                    catalog_prompt,
                    skill_schemas=schemas,
                )
                if isinstance(data, dict) and data.get("steps"):
                    data = sanitize_workflow_dict(
                        data,
                        skill_schemas=schemas,
                        known_skills=set(registry.names()),
                        aliases=SKILL_ALIASES,
                    )
                    if data.get("steps"):
                        return json.dumps(data)
            except Exception:
                pass
        except Exception:
            pass
        return _offline_compile(plan, catalog_prompt)

    cfd_agent = Agent(
        registry=registry,
        catalog=loader.catalog,
        name="cfd_agent",
        description=(
            "HVAC CFD airflow duct diffuser pressure drop RANS "
            "k-omega turbulence damper thermal comfort uniformity"
        ),
        llm=llm,
        compile_llm_call=compile_with_fallback,
        knowledge_store=knowledge,
        knowledge_trigger="soft",
    )

    agent_reg = AgentRegistry()
    agent_reg.register(cfd_agent)

    desk = Agent(
        registry=SkillRegistry(),
        catalog=[],
        name="engineering_desk",
        description="routes engineering CFD HVAC airflow requests",
        llm=llm,
        agent_registry=agent_reg,
        compile_llm_call=lambda plan, cat: json.dumps({"steps": []}),
    )
    status_parts.append("route=engineering_desk→cfd_agent")
    return desk, " | ".join(status_parts)
