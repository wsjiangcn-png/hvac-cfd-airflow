"""Style D — Hierarchical process tree on HVAC composites.

  streamlit run app/run_ui_process_tree.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ui_bridge import DEFAULT_INPUTS_JSON, DEFAULT_PROCESS, provide_registry

try:
    from agent_skill_ui.styles.process_tree import run_process_tree
except ModuleNotFoundError as err:
    name = getattr(err, "name", None) or ""
    if name == "agent_skill_ui" or str(name).startswith("agent_skill_ui"):
        raise SystemExit(
            "Missing package 'agent_skill_ui'. Install into this same venv:\n"
            "  pip install -e ~/Projects/agent-skill-ui\n"
            "  pip install -e '.[gui]'\n"
            "Then: streamlit run app/run_ui_process_tree.py"
        ) from err
    raise

if __name__ == "__main__":
    run_process_tree(
        provide_registry=provide_registry,
        title="HVAC CFD — Process tree",
        caption="Style D · expand/collapse nested HVAC pipelines",
        default_root=DEFAULT_PROCESS,
        default_inputs_json=DEFAULT_INPUTS_JSON,
    )
