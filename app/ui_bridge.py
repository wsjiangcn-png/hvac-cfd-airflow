"""
Wire HVAC agents to agent-skill-ui (Prompt / Assembler / Integrator).

  pip install -e ~/Projects/Agent-Skill-Framework
  pip install -e ~/Projects/agent-skill-ui
  pip install -e ".[gui]"

  streamlit run app/run_ui_prompt.py
  streamlit run app/run_ui_assembler.py
  streamlit run app/run_ui_integrator.py
  streamlit run app/run_ui_launcher.py
"""
from __future__ import annotations

from typing import Any

from app.agents import build_system

# Prefer these composites in Style A / C defaults
DEFAULT_PROCESS = "hvac_airflow_pipeline"
DEFAULT_INPUTS_JSON = """{
  "case_name": "commercial_hvac",
  "inlet_mass_flow_kg_s": 2.5,
  "outlet_pressure_Pa": 0.0,
  "max_delta_p_Pa": 150.0,
  "min_uniformity": 0.75
}"""

PRESETS = {
    "Baseline RANS + metrics": (
        "Run steady RANS k-ω SST on the multi-branch HVAC duct network "
        "and report pressure drop and diffuser uniformity"
    ),
    "Optimize dampers": (
        "Optimize airflow with damper adjustments to reduce pressure drop "
        "and improve thermal comfort"
    ),
}


def build_system_ui() -> tuple[Any, str]:
    """``(agent, status)`` for Style B Prompt desk."""
    return build_system()


def provide_registry() -> tuple[Any, list[Any], str]:
    """
    ``(registry, catalog, status)`` for Style C / A.

    Desk routes to ``cfd_agent``; skills live on the specialist registry.
    """
    desk, status = build_system()
    specialist = _first_skilled_agent(desk)
    if specialist is None:
        return desk.registry, list(desk.catalog or []), status
    label = getattr(specialist, "name", "specialist")
    return (
        specialist.registry,
        list(specialist.catalog or []),
        f"{status} | ui-registry={label}",
    )


def _first_skilled_agent(desk: Any) -> Any | None:
    reg = getattr(desk, "agent_registry", None)
    if reg is None:
        return None
    agents = getattr(reg, "_agents", None) or []
    for agent in agents:
        names = []
        try:
            names = list(agent.registry.names())
        except Exception:
            pass
        if names:
            return agent
    return agents[0] if agents else None
