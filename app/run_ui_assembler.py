"""Style C — Skill assembler on HVAC registry.

  cd ~/Projects/hvac-cfd-airflow
  pip install -e ~/Projects/agent-skill-ui
  pip install -e ".[gui]"
  streamlit run app/run_ui_assembler.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ui_bridge import DEFAULT_INPUTS_JSON, DEFAULT_PROCESS, provide_registry

try:
    from agent_skill_ui.styles.assembler import run_assembler
except ModuleNotFoundError as exc:
    if exc.name == "agent_skill_ui" or (exc.name and exc.name.startswith("agent_skill_ui")):
        raise SystemExit(
            "Missing package 'agent_skill_ui'. Install into this same venv:\n"
            "  pip install -e ~/Projects/agent-skill-ui\n"
            "  pip install -e '.[gui]'\n"
            "Then: streamlit run app/run_ui_assembler.py"
        ) from exc
    raise

if __name__ == "__main__":
    run_assembler(
        provide_registry=provide_registry,
        title="HVAC CFD — Skill assembler",
        caption="Style C · no LLM · pick HVAC skills",
        default_selection=[DEFAULT_PROCESS],
        default_inputs_json=DEFAULT_INPUTS_JSON,
    )
