# HVAC CFD Airflow — Play package

Optimize airflow in a commercial **HVAC multi-branch duct** network (steady RANS k-ω SST stubs) on the Agentic Engineering Desk.

**Copyright © 2026 Wei-Shan Chiang.** Personal intellectual property; independent of any former employer.

---

## Quick start

```bash
python3 install.py
# Windows: install.bat

source .venv/bin/activate          # Windows: .venv\Scripts\activate
python run_demo.py
python -m app.main
```

### Optional UI (Styles B / C / A)

From the evaluation share pack, also install `04-ui/agent_skill_ui-*.whl`:

```bash
python install.py --gui
pip install path/to/agent_skill_ui-*.whl
streamlit run app/run_ui_prompt.py
streamlit run app/run_ui_assembler.py
streamlit run app/run_ui_integrator.py
```

---

## What you will see

1. Build duct CFD case (geometry + BCs).
2. Steady RANS solve → ΔP, uniformity, turbulence near bends.
3. Optional damper adjustment + re-solve + metrics.
4. `passed` compares results to pressure / uniformity targets.

`passed: false` means **targets were missed** (e.g. ΔP a bit high), not a software crash.

See `EXPLORE_SCENARIOS.md`.
