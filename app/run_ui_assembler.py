"""Style C — Skill assembler on HVAC registry.

  cd ~/Projects/hvac-cfd-airflow
  streamlit run app/run_ui_assembler.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Repo root must be on sys.path so `import app.*` works under Streamlit
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ui_bridge import DEFAULT_INPUTS_JSON, DEFAULT_PROCESS, provide_registry
from agent_skill_ui.styles.assembler import run_assembler

if __name__ == "__main__":
    run_assembler(
        provide_registry=provide_registry,
        title="HVAC CFD — Skill assembler",
        caption="Style C · no LLM · pick HVAC skills",
        default_selection=[DEFAULT_PROCESS],
        default_inputs_json=DEFAULT_INPUTS_JSON,
    )
