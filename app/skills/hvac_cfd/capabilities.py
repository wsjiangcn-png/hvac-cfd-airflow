"""HVAC duct CFD capabilities (demo RANS metrics — swap run_rans_cfd for real solver/MCP later).

SkillDesk connector: write_hvac_artifact always leaves durable JSON+CSV under results/.

Schema convention for agent-skill-ui I/O filter:
  - "field": "float"     → required
  - "field": "float?"    → optional (still accepted at runtime)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from agent_skill_framework import capability, composite


def _f(x, default: float) -> float:
    try:
        return float(x) if x is not None else default
    except (TypeError, ValueError):
        return default


@capability(
    name="build_duct_case",
    description="Build multi-branch HVAC duct CFD case (geometry + boundary conditions)",
    input_schema={
        "case_name": "str",
        "inlet_mass_flow_kg_s": "float",
        "outlet_pressure_Pa": "float?",
    },
    output_schema={
        "ok": "bool",
        "case_file": "str",
        "n_branches": "int",
        "inlet_mass_flow_kg_s": "float",
        "outlet_pressure_Pa": "float",
        "turbulence_model": "str",
        "output": "str",
    },
)
def build_duct_case(input: dict) -> dict:
    name = input.get("case_name") or "hvac_duct"
    mdot = _f(input.get("inlet_mass_flow_kg_s"), 2.5)
    p_out = _f(input.get("outlet_pressure_Pa"), 0.0)
    return {
        "ok": True,
        "case_file": f"{name}.cas",
        "n_branches": 4,
        "inlet_mass_flow_kg_s": mdot,
        "outlet_pressure_Pa": p_out,
        "turbulence_model": "k-omega-SST",
        "output": f"Case '{name}' ready (RANS k-ω SST, mdot={mdot} kg/s)",
    }


@capability(
    name="run_rans_cfd",
    description=(
        "Steady RANS CFD solve with k-ω SST on an HVAC duct case; "
        "returns pressure drop, uniformity, and turbulence intensity"
    ),
    input_schema={
        "case_file": "str",
        "inlet_mass_flow_kg_s": "float",
        "damper_fractions": "list?",
    },
    output_schema={
        "ok": "bool",
        "case_file": "str",
        "inlet_mass_flow_kg_s": "float",
        "delta_p_Pa": "float",
        "uniformity_index": "float",
        "max_ti_near_bends": "float",
        "branch_delta_p_Pa": "list",
        "velocity_contour": "str",
        "pressure_map": "str",
        "output": "str",
    },
)
def run_rans_cfd(input: dict) -> dict:
    mdot = _f(input.get("inlet_mass_flow_kg_s"), 2.5)
    fracs = input.get("damper_fractions") or []
    balance = 1.0
    if isinstance(fracs, list) and fracs:
        balance = sum(_f(x, 0.5) for x in fracs) / max(len(fracs), 1)
        balance = max(0.4, min(1.2, balance))
    dp = round((80.0 + 12.0 * (mdot ** 2)) / balance, 1)
    uni = round(max(0.55, min(0.98, 0.92 - 0.04 * mdot + 0.08 * (balance - 0.7))), 3)
    ti = round(0.08 + 0.01 * mdot, 3)
    branches = [round(dp * f, 1) for f in (0.28, 0.22, 0.30, 0.20)]
    return {
        "ok": True,
        "case_file": input.get("case_file"),
        "inlet_mass_flow_kg_s": mdot,
        "delta_p_Pa": dp,
        "uniformity_index": uni,
        "max_ti_near_bends": ti,
        "branch_delta_p_Pa": branches,
        "solver_mode": "stub",
        "velocity_contour": "results/velocity.png",
        "pressure_map": "results/pressure.png",
        "output": f"RANS done: ΔP={dp} Pa, UI={uni}, TI_max={ti}",
    }


@capability(
    name="evaluate_hvac_metrics",
    description="Score pressure drop, diffuser uniformity, and bend turbulence vs targets",
    input_schema={
        "delta_p_Pa": "float",
        "uniformity_index": "float",
        "max_ti_near_bends": "float",
        "max_delta_p_Pa": "float?",
        "min_uniformity": "float?",
    },
    output_schema={
        "ok": "bool",
        "passed": "bool",
        "score": "float",
        "delta_p_Pa": "float",
        "uniformity_index": "float",
        "max_ti_near_bends": "float",
        "output": "str",
    },
)
def evaluate_hvac_metrics(input: dict) -> dict:
    dp = _f(input.get("delta_p_Pa"), 999.0)
    uni = _f(input.get("uniformity_index"), 0.0)
    ti = _f(input.get("max_ti_near_bends"), 1.0)
    max_dp = _f(input.get("max_delta_p_Pa"), 150.0)
    min_uni = _f(input.get("min_uniformity"), 0.75)
    passed = dp <= max_dp and uni >= min_uni and ti <= 0.15
    score = round(0.5 * max(0.0, (max_dp - dp) / max_dp) + 0.5 * uni, 3)
    return {
        "ok": True,
        "passed": passed,
        "score": score,
        "delta_p_Pa": dp,
        "uniformity_index": uni,
        "max_ti_near_bends": ti,
        "output": f"passed={passed} score={score} (ΔP={dp} Pa, UI={uni}, TI={ti})",
    }


@capability(
    name="adjust_dampers",
    description="Propose damper positions to balance branches and reduce pressure drop",
    input_schema={
        "branch_delta_p_Pa": "list",
        "uniformity_index": "float?",
    },
    output_schema={
        "ok": "bool",
        "damper_fractions": "list",
        "output": "str",
    },
)
def adjust_dampers(input: dict) -> dict:
    branches = input.get("branch_delta_p_Pa") or [1.0, 1.0, 1.0, 1.0]
    vals = [_f(b, 1.0) for b in branches]
    total = sum(vals) or 1.0
    fracs = [round(min(1.0, 0.45 + 0.55 * (b / total)), 3) for b in vals]
    return {
        "ok": True,
        "damper_fractions": fracs,
        "output": f"Damper fractions {fracs}",
    }


@capability(
    name="write_hvac_artifact",
    description="Write HVAC airflow results JSON + CSV under results/ (SkillDesk durable artifact)",
    input_schema={
        "artifact_dir": "str?",
        "case_file": "str?",
        "inlet_mass_flow_kg_s": "float?",
        "delta_p_Pa": "float?",
        "uniformity_index": "float?",
        "max_ti_near_bends": "float?",
        "passed": "bool?",
        "score": "float?",
        "damper_fractions": "list?",
        "solver_mode": "str?",
    },
    output_schema={
        "artifact_json": "str",
        "artifact_csv": "str",
        "ok": "bool",
        "output": "str",
    },
)
def write_hvac_artifact(input: dict) -> dict:
    out_dir = Path(str(input.get("artifact_dir") or "results/hvac_cfd"))
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "case_file": input.get("case_file"),
        "inlet_mass_flow_kg_s": input.get("inlet_mass_flow_kg_s"),
        "delta_p_Pa": input.get("delta_p_Pa"),
        "uniformity_index": input.get("uniformity_index"),
        "max_ti_near_bends": input.get("max_ti_near_bends"),
        "passed": input.get("passed"),
        "score": input.get("score"),
        "damper_fractions": input.get("damper_fractions"),
        "solver_mode": input.get("solver_mode") or "stub",
        "product": "hvac-cfd-airflow",
        "platform": "SkillDesk",
    }
    json_path = out_dir / "hvac_results.json"
    csv_path = out_dir / "hvac_results.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "value"])
        for k, v in payload.items():
            w.writerow([k, v])
    return {
        "ok": True,
        "artifact_json": str(json_path),
        "artifact_csv": str(csv_path),
        "artifact_dir": str(out_dir),
        "passed": input.get("passed"),
        "score": input.get("score"),
        "delta_p_Pa": input.get("delta_p_Pa"),
        "output": f"Wrote HVAC artifacts {json_path} and {csv_path}",
    }


hvac_airflow_pipeline = composite(
    name="hvac_airflow_pipeline",
    description=(
        "Full HVAC airflow study: build duct case → steady RANS k-ω SST → "
        "evaluate metrics → write artifacts"
    ),
    steps=[
        "build_duct_case",
        "run_rans_cfd",
        "evaluate_hvac_metrics",
        "write_hvac_artifact",
    ],
    input_schema={
        "case_name": "str",
        "inlet_mass_flow_kg_s": "float",
        "outlet_pressure_Pa": "float?",
        "max_delta_p_Pa": "float?",
        "min_uniformity": "float?",
    },
    output_schema={
        "ok": "bool",
        "passed": "bool",
        "artifact_json": "str",
        "output": "str",
    },
)

hvac_optimize_dampers_pipeline = composite(
    name="hvac_optimize_dampers_pipeline",
    description=(
        "Optimize airflow distribution: CFD baseline → adjust dampers → "
        "re-solve → evaluate → write artifacts"
    ),
    steps=[
        "build_duct_case",
        "run_rans_cfd",
        "adjust_dampers",
        "run_rans_cfd",
        "evaluate_hvac_metrics",
        "write_hvac_artifact",
    ],
    input_schema={
        "case_name": "str",
        "inlet_mass_flow_kg_s": "float",
        "max_delta_p_Pa": "float?",
        "min_uniformity": "float?",
    },
    output_schema={
        "ok": "bool",
        "passed": "bool",
        "artifact_json": "str",
        "output": "str",
    },
)
