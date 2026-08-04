#!/usr/bin/env python3
"""Create .venv and install framework wheel (any OS)."""
from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
DIST = ROOT / "dist"


def _python() -> Path:
    if sys.platform == "win32":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--gui",
        action="store_true",
        help="Also install streamlit for agent-skill-ui entrypoints",
    )
    args = p.parse_args()

    if not VENV.is_dir():
        print("Creating", VENV)
        venv.create(VENV, with_pip=True)

    py = _python()
    wheels = sorted(DIST.glob("agent_skill_framework*.whl"))
    if not wheels:
        print("ERROR: no agent_skill_framework*.whl under dist/", file=sys.stderr)
        return 1
    wheel = wheels[-1]
    print("Installing", wheel.name)
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(py), "-m", "pip", "install", str(wheel)])
    print("App surface is ./app (no separate package install required).")

    if args.gui:
        print("Installing streamlit …")
        subprocess.check_call([str(py), "-m", "pip", "install", "streamlit>=1.28"])
        print("UI: also pip install agent_skill_ui-*.whl from the share pack 04-ui/")

    print()
    print("Activate:")
    if sys.platform == "win32":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("Then:")
    print("  python run_demo.py")
    print("  python -m app.main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
