"""Style B — Prompt desk on HVAC agents.

  cd ~/Projects/hvac-cfd-airflow
  streamlit run app/run_ui_prompt.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
