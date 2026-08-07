"""Engineering desk + CFD specialist for HVAC airflow optimization.

Skill ownership (ForgeDesk left rail):
  - **Desk** (`engineering_desk`): empty registry — routes only.
  - **cfd_agent**: all HVAC skills (case → RANS → metrics → damper pipelines).

This product has a *single* domain specialist, so "Skills (this agent)" for
CFD matches the product-wide Skill Repo by design. Split further only if you
add more specialists (e.g. mesh vs solve vs post).

Runtime requires a valid AFIPER1 license (edition=hvac-cfd or full-trial),
same hard-gate model as Bracket FEA.
"""
from __future__ import annotations

import json
import os
import re
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

from app.license_gate import exit_on_license_error
from app.skill_aliases import SKILL_ALIASES

APP_ROOT = Path(__file__).resolve().parent
HVAC = APP_ROOT / "skills" / "hvac_cfd"

# Pipelines safe to schedule as a single Workflow step (expand inside CompositeSkill)
_SAFE_PIPELINES = frozenset({
    "hvac_airflow_pipeline",
    "hvac_optimize_dampers_pipeline",
})

_REF_RE = re.compile(r"\$(?P<step>[A-Za-z0-9_]+)\.output(?:\.|$)")


def _wants_optimize(text: str) -> bool:
    t = text.lower()
    keys = ("optim", "damper", "balance", "reduce pressure", "improve comfort")
    return any(k in t for k in keys)


def _offline_compile(plan: Plan, catalog_prompt: str = "") -> str:
    """Deterministic single-step pipeline (composite expands internally)."""
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


def _workflow_is_safe(data: dict, known_skills: set[str]) -> bool:
    """
    Accept only:
      - exactly one step whose skill is a known SAFE pipeline, or
      - multi-step graphs where every $ref targets a step id listed in depends_on
        and step ids look like s1, s2, ... (not skill names).
    """
    steps = data.get("steps") or []
    if not steps:
        return False

    if len(steps) == 1:
        sk = steps[0].get("skill")
        return sk in _SAFE_PIPELINES and sk in known_skills

    ids = {str(s.get("id")) for s in steps if s.get("id")}
    # Reject skill-named step ids (common LLM failure mode)
    for sid in ids:
        if sid in known_skills:
            return False
        if not re.fullmatch(r"s\d+", sid):
            return False

    for s in steps:
        deps = set(s.get("depends_on") or [])
        payload = s.get("input") or {}
        skill = s.get("skill")
        if skill not in known_skills:
            return False
        for v in payload.values():
            if not isinstance(v, str) or not v.startswith("$"):
                continue
            m = _REF_RE.match(v)
            if not m:
                return False
            ref = m.group("step")
            if ref not in ids or ref not in deps:
                return False
    return True


def build_system() -> tuple[Agent, str]:
    exit_on_license_error()

    # Single domain registry: all HVAC skills live on cfd_agent only
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

    # Default: offline composite only (reliable demos).
    # Set HVAC_LLM_COMPILE=1 to allow validated LLM workflows.
    use_llm_compile = os.environ.get("HVAC_LLM_COMPILE", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    status_parts.append(
        "compile=llm+guard" if (llm and use_llm_compile) else "compile=offline-pipeline"
    )

    schemas = {s.name: (s.input_schema or {}) for s in loader.catalog}
    known = set(registry.names())

    def compile_with_fallback(plan: Plan, catalog_prompt: str) -> str:
        offline = _offline_compile(plan, catalog_prompt)

        if not use_llm_compile or llm is None:
            return offline

        try:
            try:
                data = llm.compile_plan(
                    plan.goal,
                    plan.intents,
                    catalog_prompt,
                    skill_schemas=schemas,
                    aliases=SKILL_ALIASES,
                )
            except TypeError:
                data = llm.compile_plan(
                    plan.goal,
                    plan.intents,
                    catalog_prompt,
                    skill_schemas=schemas,
                )
            if not isinstance(data, dict):
                return offline
            data = sanitize_workflow_dict(
                data,
                skill_schemas=schemas,
                known_skills=known,
                aliases=SKILL_ALIASES,
            )
            if _workflow_is_safe(data, known):
                return json.dumps(data)
        except Exception:
            pass
        return offline

    cfd_agent = Agent(
        registry=registry,
        catalog=loader.catalog,
        name="cfd_agent",
        description=(
            "HVAC CFD airflow duct diffuser pressure drop RANS "
            "k-omega turbulence damper thermal comfort uniformity"
        ),
        llm=llm,  # still used for plan() goal/intents when available
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
    status_parts.append(
        f"route=engineering_desk→cfd_agent (cfd_skills={len(known)})"
    )
    return desk, " | ".join(status_parts)
