"""Style A — Process integrator on HVAC composites.

  cd ~/Projects/hvac-cfd-airflow
  streamlit run app/run_ui_integrator.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ui_bridge import DEFAULT_INPUTS_JSON, DEFAULT_PROCESS, provide_registry
from agent_skill_ui.styles.integrator import run_integrator

if __name__ == "__main__":
    run_integrator(
        provide_registry=provide_registry,
        title="HVAC CFD — Process integrator",
        caption="Style A · pin pipeline · offline run",
        default_process=DEFAULT_PROCESS,
        default_inputs_json=DEFAULT_INPUTS_JSON,
    )
