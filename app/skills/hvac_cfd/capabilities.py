"""HVAC duct CFD capabilities (stubs — swap run_rans_cfd for real solver/MCP later)."""
from __future__ import annotations

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
        "outlet_pressure_Pa": "float",
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
        "damper_fractions": "list",
    },
    output_schema={
        "ok": "bool",
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
        "max_delta_p_Pa": "float",
        "min_uniformity": "float",
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
        "uniformity_index": "float",
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


# IMPORTANT: assign composites to module globals so BundleLoader can discover them
hvac_airflow_pipeline = composite(
    name="hvac_airflow_pipeline",
    description=(
        "Full HVAC airflow study: build duct case → steady RANS k-ω SST → "
        "evaluate pressure drop, uniformity, and turbulence"
    ),
    steps=["build_duct_case", "run_rans_cfd", "evaluate_hvac_metrics"],
    input_schema={
        "case_name": "str",
        "inlet_mass_flow_kg_s": "float",
        "outlet_pressure_Pa": "float",
        "max_delta_p_Pa": "float",
        "min_uniformity": "float",
    },
    output_schema={"ok": "bool", "passed": "bool", "output": "str"},
)

hvac_optimize_dampers_pipeline = composite(
    name="hvac_optimize_dampers_pipeline",
    description=(
        "Optimize airflow distribution: CFD baseline → adjust dampers → "
        "re-solve → evaluate metrics"
    ),
    steps=[
        "build_duct_case",
        "run_rans_cfd",
        "adjust_dampers",
        "run_rans_cfd",
        "evaluate_hvac_metrics",
    ],
    input_schema={
        "case_name": "str",
        "inlet_mass_flow_kg_s": "float",
        "max_delta_p_Pa": "float",
        "min_uniformity": "float",
    },
    output_schema={"ok": "bool", "passed": "bool", "output": "str"},
)
