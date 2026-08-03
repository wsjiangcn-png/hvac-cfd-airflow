"""Style B — Prompt desk on HVAC agents.  streamlit run app/run_ui_prompt.py"""
from __future__ import annotations

from app.ui_bridge import PRESETS, build_system_ui

from agent_skill_ui.styles.prompt_desk import run_prompt_desk

if __name__ == "__main__":
    run_prompt_desk(
        build_system=build_system_ui,
        title="HVAC CFD — Prompt desk",
        caption="Style B · agent-skill-ui · hvac-cfd-airflow",
        default_prompt=PRESETS["Baseline RANS + metrics"],
        presets=PRESETS,
        page_icon="🌬️",
    )
