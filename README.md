# hvac-cfd-airflow

Application on [agent-skill-framework](https://github.com/wsjiangcn-png/Agent-Skill-Framework) for:

**CFD — HVAC System Airflow Optimization** (steady RANS, k-ω SST).

Scaffolded from [agent-skill-devkit](https://github.com/wsjiangcn-png/agent-skill-devkit); domain code lives only here.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install agent_skill_framework-*.whl   # or: pip install -e ../Agent-Skill-Framework
pip install -e .
```

## Run

```bash
python -m app.main
python -m app.main "Optimize airflow with damper adjustments to reduce pressure drop"
```

- Agents: `engineering_desk` → `cfd_agent`
- Pipelines: `hvac_airflow_pipeline`, `hvac_optimize_dampers_pipeline`
- Solvers are **stubs** for demo; replace `run_rans_cfd` with a real CFD backend later

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) | **Full build steps, architecture, troubleshooting, checklist** |
| [scenarios/hvac_duct_airflow.md](scenarios/hvac_duct_airflow.md) | Scenario description and skill mapping |
