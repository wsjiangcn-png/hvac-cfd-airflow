# Implementation Report — HVAC CFD Airflow Application

**Product:** `hvac-cfd-airflow`  
**Scenario:** CFD — HVAC System Airflow Optimization (steady RANS, k-ω SST)  
**Library:** [agent-skill-framework](https://github.com/wsjiangcn-png/Agent-Skill-Framework) v0.9.x  
**Scaffold:** [agent-skill-devkit](https://github.com/wsjiangcn-png/agent-skill-devkit)  
**Repo:** https://github.com/wsjiangcn-png/hvac-cfd-airflow  

This document records **how this application was built** and **how to run, extend, and maintain it**. It is the primary user guide for developers taking over or repeating the same pattern for a new domain.

---

## 1. Objective

Build a **separate product application** (not inside the framework repo) that:

- Uses `agent-skill-framework` as an installable dependency  
- Models a commercial **HVAC multi-branch duct** airflow study  
- Exposes agents + skills for:
  - Steady RANS CFD (k-ω SST, stubbed)
  - Branch pressure drop, diffuser uniformity, turbulence near bends
  - Damper adjustment and a simple optimize pipeline  
- Routes `engineering_desk` → specialized `cfd_agent`  

**Out of scope for v0.1:** production CFD solvers, Streamlit GUI, customer trial zip (those follow the same patterns as `bracket-static-fea`).

---

## 2. Ecosystem context

| Repo | Role |
|------|------|
| **Agent-Skill-Framework** | Pure library (Agent, Skill, Workflow, LLM, MCP, cache, …) |
| **agent-skill-devkit** | Docs + `scaffold_app.py` + minimal template |
| **bracket-static-fea** | Full FEA product example (reference only) |
| **hvac-cfd-airflow** (this) | HVAC CFD product application |

Starting from the framework **share pack** (`deploy/dist/share/`):

1. `01-library/` — install the `.whl`  
2. `03-devkit/` — scaffold a new app  
3. `02-product-trial/` — optional Bracket demo (not required for HVAC)

You do **not** need to fork the framework to implement HVAC.

---

## 3. Completed steps (chronological)

### Step A — Prerequisites

1. Install or clone **agent-skill-framework** (`pip install -e` or `.whl`).  
2. Clone **agent-skill-devkit**.  
3. Confirm: `python -c "from agent_skill_framework import __version__; print(__version__)"`.

### Step B — Scaffold a new app repo

```bash
cd ~/Projects/agent-skill-devkit
python scripts/scaffold_app.py \
  --name hvac_cfd_airflow \
  --out ~/Projects/hvac-cfd-airflow

cd ~/Projects/hvac-cfd-airflow
python3 -m venv .venv && source .venv/bin/activate
pip install -e ~/Projects/Agent-Skill-Framework
pip install -e .
```

### Step C — Git hygiene + remote

1. Add `.gitignore` (exclude `__pycache__/`, `*.egg-info/`, `.venv/`).  
2. `git init` and initial commit of the scaffold.  
3. Create private GitHub repo `wsjiangcn-png/hvac-cfd-airflow`.  
4. Push with **HTTPS + PAT** if SSH keys are not configured:

```bash
git remote set-url origin https://github.com/wsjiangcn-png/hvac-cfd-airflow.git
git push -u origin main
```

### Step D — Domain skill bundle

Created `app/skills/hvac_cfd/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Knowledge + trigger keywords (not executed) |
| `capabilities.py` | Atomic skills + composite pipelines |

**Atomic skills**

| Name | Role |
|------|------|
| `build_duct_case` | Case name, inlet mass flow, outlet pressure |
| `run_rans_cfd` | Stub RANS (k-ω SST): ΔP, uniformity, TI, branch ΔP |
| `evaluate_hvac_metrics` | Pass/fail vs targets |
| `adjust_dampers` | Propose damper fractions from branch ΔP |

**Composites** (must be **assigned** to module-level names so `BundleLoader` registers them):

| Name | Steps |
|------|--------|
| `hvac_airflow_pipeline` | build → RANS → evaluate |
| `hvac_optimize_dampers_pipeline` | build → RANS → dampers → RANS → evaluate |

> **Lesson learned:** `composite(...)` without assignment discards the skill object; use `name = composite(...)`.

### Step E — Agents and aliases

| File | Purpose |
|------|---------|
| `app/skill_aliases.py` | Map LLM inventions (`run_cfd`, …) → real pipelines |
| `app/agents.py` | Load bundle; `cfd_agent`; desk routes to it |
| `app/main.py` | CLI entrypoint |

Routing:

```text
User prompt → engineering_desk → cfd_agent → plan/compile → Executor
```

Offline compile picks:

- `hvac_optimize_dampers_pipeline` if the prompt suggests optimize/damper/balance  
- else `hvac_airflow_pipeline`

### Step F — LLM compile hardening

**Problem:** Ollama sometimes emitted invalid refs such as `$build_duct_case.output.case_file` (skill name instead of step id `$s1`).

**Fix in `app/agents.py`:**

- Prefer a **single composite step** workflow  
- Accept LLM output only if one known skill **or** all `$…` refs name real step ids  
- Otherwise fall back to offline compile  

### Step G — Remove template hello skill

Deleted `app/skills/hello/` once HVAC loaded successfully.

### Step H — Scenario documentation

- `scenarios/hvac_duct_airflow.md` — scenario text + skill mapping  
- This report — end-to-end implementation guide  

---

## 4. Final repository layout

```text
hvac-cfd-airflow/
├── README.md
├── pyproject.toml
├── docs/
│   └── IMPLEMENTATION_REPORT.md    ← this file
├── scenarios/
│   └── hvac_duct_airflow.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── agents.py
    ├── skill_aliases.py
    └── skills/
        └── hvac_cfd/
            ├── SKILL.md
            └── capabilities.py
```

---

## 5. How to run (users)

```bash
cd ~/Projects/hvac-cfd-airflow
python3 -m venv .venv && source .venv/bin/activate

# library (wheel from share pack OR editable clone)
pip install /path/to/agent_skill_framework-0.9.0-py3-none-any.whl
# or: pip install -e ~/Projects/Agent-Skill-Framework

pip install -e .

python -m app.main
python -m app.main "Optimize airflow with damper adjustments to reduce pressure drop"
```

Optional LLM (plan/compile assist; offline fallback always available):

```bash
ollama serve
ollama pull llama3.2
```

**Expected status line:**

```text
skills=[adjust_dampers, build_duct_case, evaluate_hvac_metrics,
        hvac_airflow_pipeline, hvac_optimize_dampers_pipeline, run_rans_cfd]
| llm=… | route=engineering_desk→cfd_agent
```

**Expected result fields (stub physics):** `ok`, `passed`, `delta_p_Pa`, `uniformity_index`, `max_ti_near_bends`, `score`, `output`, …

---

## 6. Scenario → skill mapping

| Scenario need | Implementation |
|---------------|----------------|
| Multi-branch duct + BC | `build_duct_case` |
| Steady RANS, k-ω SST | `run_rans_cfd` (stub) |
| Branch ΔP, uniformity, TI | outputs of `run_rans_cfd` + `evaluate_hvac_metrics` |
| Damper effectiveness | `adjust_dampers` + second `run_rans_cfd` in optimize pipeline |
| Full study | `hvac_airflow_pipeline` |
| Optimize distribution | `hvac_optimize_dampers_pipeline` |

---

## 7. Design decisions

1. **App repo ≠ library repo** — domain skills and agents stay product-owned.  
2. **Stub CFD first** — proves agent/skill wiring before solver integration.  
3. **Composite pipelines** — hide multi-step detail from the top-level Workflow when offline.  
4. **Strict compile fallback** — demos stay reliable when the LLM mis-wires `$refs`.  
5. **Aliases** — absorb common LLM name inventions without renaming skills.  

---

## 8. Known limitations (v0.1)

| Item | Notes |
|------|--------|
| Physics | Analytic stub, not mesh-based RANS |
| Contours | Placeholder paths (`results/velocity.png`, …) |
| GUI | Not included |
| Trial license / customer zip | Not included (see framework + Bracket packaging) |
| LLM multi-step workflows | Accepted only if `$sN` refs validate; else offline composite |

---

## 9. Recommended next steps

1. **Real solver** — replace `run_rans_cfd` body with OpenFOAM, Fluent, or an MCP station tool.  
2. **OptimizationLoop** — multi-iteration damper search using framework `OptimizationLoop`.  
3. **GUI** — Streamlit scenario runner (pattern from `bracket-static-fea`).  
4. **Contracts / cache** — `CapabilityRegistry` + `RunCache` for selective re-execution.  
5. **Customer pack** — wheel-only zip of this app + framework wheel + license.  

---

## 10. Troubleshooting

| Symptom | Action |
|---------|--------|
| `No module named 'agent_skill_framework'` | Install library wheel or `pip install -e` framework |
| `No module named 'app'` | `pip install -e .` from app root; run `python -m app.main` |
| `source: .venv/bin/activate` missing | `python3 -m venv .venv` then activate |
| `KeyError: Reference $….output` | Pull latest `agents.py` (invalid LLM refs → offline fallback) |
| Pipeline skills missing from `skills=[…]` | Ensure composites are assigned: `name = composite(...)` |
| SSH `Permission denied (publickey)` | Use HTTPS remote + PAT, or add an SSH key to GitHub |

---

## 11. Checklist — “done” for v0.1

- [x] Separate private GitHub application repo  
- [x] Depends on agent-skill-framework only (no framework source vendored)  
- [x] HVAC skill bundle (knowledge + capabilities)  
- [x] Composite study + optimize pipelines registered  
- [x] Desk → CFD sub-agent routing  
- [x] Offline compile + LLM fallback with ref validation  
- [x] Scenario doc + this implementation report  
- [x] CLI runnable: `python -m app.main`  

---

## 12. Quick reference commands

```bash
# install
pip install -e ~/Projects/Agent-Skill-Framework && pip install -e .

# baseline study
python -m app.main

# damper optimization path
python -m app.main "Optimize airflow with damper adjustments to reduce pressure drop"

# pull latest guidance / code
git pull origin main
```

For framework packaging and multi-product share folders, see Agent-Skill-Framework `docs/PACKAGING.md` and `deploy/dist/share/README-START-HERE.txt`.
