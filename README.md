# hvac-cfd-airflow

Application on [agent-skill-framework](https://github.com/wsjiangcn-png/Agent-Skill-Framework) for:

**CFD — HVAC System Airflow Optimization** (steady RANS, k-ω SST).

Scaffolded from [agent-skill-devkit](https://github.com/wsjiangcn-png/agent-skill-devkit); domain code lives only here.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../Agent-Skill-Framework   # or wheel (requires agent-skill-framework>=0.9.0)
pip install -e .
pip install -e ".[gui]"
```

## CLI

```bash
python -m app.main
python -m app.main "Optimize airflow with damper adjustments to reduce pressure drop"
```

## GUI — domain desk

```bash
streamlit run app/gui_app.py
```

Presets, metric cards (ΔP, uniformity, TI), workflow DAG preview.  
Use `streamlit run …` — not `python app/gui_app.py`.

## GUI — agent-skill-ui styles (optional)

Generic Style B / C / A shells on the same HVAC agents:

```bash
pip install -e ../agent-skill-ui
streamlit run app/run_ui_prompt.py       # B — NL prompt desk
streamlit run app/run_ui_assembler.py    # C — skill picker
streamlit run app/run_ui_integrator.py   # A — pin pipeline
```

Optional concept edges (Style A/C):  
`export AGENT_SKILL_ONTOLOGY=../Agent-Skill-Framework/examples/ontology/hvac_concepts.json`

Bridge: `app/ui_bridge.py` (`build_system_ui`, `provide_registry`).

- Agents: `engineering_desk` → `cfd_agent`
- Pipelines: `hvac_airflow_pipeline`, `hvac_optimize_dampers_pipeline`
- Solvers are **stubs** for demo

## Documentation

| Doc | Contents |
|------|----------|
| [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) | Full build steps |
| [scenarios/hvac_duct_airflow.md](scenarios/hvac_duct_airflow.md) | Scenario mapping |

---

## License and ownership

**Copyright © 2026 Wei-Shan Chiang. All rights reserved.**  
This software is the personal intellectual property of Wei-Shan Chiang and is independent of any former employer.  
Proprietary. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
