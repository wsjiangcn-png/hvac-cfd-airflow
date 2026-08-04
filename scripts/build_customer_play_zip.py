#!/usr/bin/env python3
"""
Build a customer **play** zip for hvac-cfd-airflow.

Layout:
  - framework wheel from sibling Agent-Skill-Framework (or FRAMEWORK_REPO)
  - product surface from this repo's app/
  - installers + run_demo.py at zip root
  - no trial license gate (play / evaluation)

Usage (from hvac-cfd-airflow root):

  python scripts/build_customer_play_zip.py
  export FRAMEWORK_REPO=/path/to/Agent-Skill-Framework

Output:
  deploy/dist/HVAC-CFD-Play-<app-version>.zip
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP_SRC = REPO / "app"
PLAY_META = REPO / "deploy" / "customer_play"
OUT_ROOT = REPO / "deploy" / "dist"

INSTALLER_FILES = (
    "install.py",
    "install.sh",
    "install.bat",
    "README.md",
    "EXPLORE_SCENARIOS.md",
    "LICENSE-PLAY.txt",
)


def _framework_repo() -> Path:
    env = os.environ.get("FRAMEWORK_REPO", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    sibling = (REPO.parent / "Agent-Skill-Framework").resolve()
    if sibling.is_dir() and (sibling / "pyproject.toml").is_file():
        return sibling
    raise SystemExit(
        "Cannot find Agent-Skill-Framework to build the wheel.\n"
        "  export FRAMEWORK_REPO=/path/to/Agent-Skill-Framework\n"
        f"  (looked for sibling {sibling})"
    )


def _app_version() -> str:
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0"


def _fw_version(fw: Path) -> str:
    text = (fw / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0"


def _build_wheel(fw: Path, staging_dist: Path) -> Path:
    staging_dist.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "pip", "wheel",
        str(fw),
        "-w", str(staging_dist),
        "--no-deps",
    ]
    print("Building framework wheel from", fw)
    subprocess.check_call(cmd, cwd=str(fw))
    wheels = sorted(staging_dist.glob("agent_skill_framework*.whl"))
    if not wheels:
        wheels = sorted(staging_dist.glob("*.whl"))
    if not wheels:
        raise SystemExit("No framework wheel produced")
    return wheels[-1]


def _copy_app(dest_app: Path) -> None:
    if not APP_SRC.is_dir():
        raise SystemExit(f"Missing app/ at {APP_SRC}")
    if dest_app.exists():
        shutil.rmtree(dest_app)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "*.egg-info")
    shutil.copytree(APP_SRC, dest_app, ignore=ignore)
    (dest_app / "README.md").write_text(
        "# HVAC CFD airflow (play surface)\n\n"
        "Commercial HVAC duct RANS demo on agent-skill-framework.\n\n"
        "Framework is the wheel under `dist/`, not source.\n\n"
        "```bash\npython install.py\npython run_demo.py\n```\n",
        encoding="utf-8",
    )


def _write_run_demo(path: Path) -> None:
    path.write_text(
        '''#!/usr/bin/env python3
"""Customer play demo — HVAC duct airflow CFD."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if (ROOT / "app").is_dir():
    sys.path.insert(0, str(ROOT))

from app.agents import build_system

CASES = [
    (
        "Baseline RANS + metrics",
        "Run steady RANS k-ω SST on the multi-branch HVAC duct network "
        "and report pressure drop and diffuser uniformity",
    ),
    (
        "Optimize dampers",
        "Optimize airflow with damper adjustments to reduce pressure drop "
        "and improve thermal comfort",
    ),
]


def main() -> int:
    for title, prompt in CASES:
        print("=" * 60)
        print(title)
        print(f"  Prompt: {prompt}")
        print("-" * 60)
        try:
            agent, status = build_system()
            print(f"  status: {status}")
            result = agent.handle(prompt)
            if isinstance(result, dict):
                for k in (
                    "passed", "score", "delta_p_Pa", "uniformity_index",
                    "max_ti_near_bends", "output", "ok",
                ):
                    if k in result:
                        print(f"  {k}: {result[k]}")
                text = json.dumps(result, indent=2, default=str)
                print(text[:2000])
                if len(text) > 2000:
                    print("  … (truncated)")
            else:
                print("  result:", result)
        except Exception as err:
            print(f"  ERROR: {type(err).__name__}: {err}")
        print()
    print("Note: passed=false means metrics missed targets, not a software crash.")
    print("Tip: streamlit run app/run_ui_assembler.py  (after pip install agent-skill-ui)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def main() -> int:
    argparse.ArgumentParser(
        description="Build HVAC CFD play zip for customer share pack"
    ).parse_args()

    fw = _framework_repo()
    app_ver = _app_version()
    fw_ver = _fw_version(fw)
    name = f"HVAC-CFD-Play-{app_ver}"
    stage = OUT_ROOT / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    dist_dir = stage / "dist"
    dist_dir.mkdir()

    wheel = _build_wheel(fw, dist_dir)
    print("Wheel:", wheel.name, f"(framework {fw_ver}, app {app_ver})")

    _copy_app(stage / "app")
    print("Packed app/")

    _write_run_demo(stage / "run_demo.py")

    for fname in INSTALLER_FILES:
        src = PLAY_META / fname
        if src.exists():
            shutil.copy2(src, stage / fname)
            print("Packed", fname)
        else:
            print("  missing meta:", fname)

    (stage / "RELEASE_NOTES.txt").write_text(
        f"HVAC CFD Airflow — Play pack (app {app_ver}, framework {fw_ver})\n"
        f"==========================================================\n\n"
        "Steady RANS k-ω SST HVAC duct demo (stub solver).\n\n"
        "Install:\n"
        "  python install.py\n"
        "  python run_demo.py\n\n"
        "Optional UI (install agent-skill-ui from share pack 04-ui):\n"
        "  streamlit run app/run_ui_prompt.py\n"
        "  streamlit run app/run_ui_assembler.py\n"
        "  streamlit run app/run_ui_integrator.py\n",
        encoding="utf-8",
    )

    zip_path = OUT_ROOT / f"{name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in stage.rglob("*"):
            if f.is_file():
                zf.write(f, arcname=str(Path(name) / f.relative_to(stage)))
    print("Created", zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
