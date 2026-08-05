"""
Launch native Engineering Desk for HVAC (PySide6).

  pip install -e ~/Projects/Agent-Skill-Framework
  pip install -e ~/Projects/agent-skill-desktop
  pip install -e .

  python -m app.run_desktop_desk
"""
from __future__ import annotations

from app.ui_bridge import (
    DEFAULT_INPUTS_JSON,
    DEFAULT_PROCESS,
    build_system_ui,
    provide_registry,
)


def main() -> int:
    from agent_skill_desktop import run_desktop_desk

    return run_desktop_desk(
        provide_registry=provide_registry,
        build_system=build_system_ui,
        title="HVAC CFD — Engineering Desk",
        default_process=DEFAULT_PROCESS,
        default_inputs_json=DEFAULT_INPUTS_JSON,
        default_order=[DEFAULT_PROCESS],
    )


if __name__ == "__main__":
    raise SystemExit(main())
