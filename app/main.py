"""CLI entry: python -m app.main \"Run RANS on HVAC ducts\"

After each run, SkillDesk writes ``results/runs/<run_id>.json`` (WP1 lineage).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

from app.agents import build_system
from app.license_gate import exit_on_license_error

try:
    from skilldesk import write_run_record
except ImportError:
    from agent_skill_framework import write_run_record

DEFAULT_PROMPT = (
    "Run steady RANS k-ω SST on the multi-branch HVAC duct network "
    "and report pressure drop and diffuser uniformity"
)


def main(prompt: str) -> dict:
    exit_on_license_error()
    agent, status = build_system()
    print(status)
    raw = agent.handle(prompt)
    result = raw if isinstance(raw, dict) else {"result": raw}

    preview = {}
    try:
        preview = agent.preview(prompt) if hasattr(agent, "preview") else {}
        if not isinstance(preview, dict):
            preview = {}
    except Exception:
        preview = {}

    summary = write_run_record(
        prompt=prompt,
        result=result,
        product="hvac-cfd",
        preview=preview,
        metadata={"physics_mode": result.get("solver_mode") or "demo"},
        runs_dir=_ROOT / "results" / "runs",
    )
    if not summary.get("skipped"):
        print(f"run_record: {summary.get('path')}")
        print(f"physics_mode: {summary.get('physics_mode')}")

    return result


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]).strip() or DEFAULT_PROMPT
    out = main(prompt)
    print(json.dumps(out, indent=2, default=str))
