"""
Streamlit GUI for HVAC CFD airflow desk.

  pip install -e ".[gui]"
  streamlit run app/gui_app.py
"""
from __future__ import annotations

import json
from typing import Any

import streamlit as st

from app.agents import build_system

PRESETS: dict[str, str] = {
    "Baseline study (RANS + metrics)": (
        "Run steady RANS k-ω SST on the multi-branch HVAC duct network "
        "and report pressure drop and diffuser uniformity"
    ),
    "Optimize dampers": (
        "Optimize airflow with damper adjustments to reduce pressure drop "
        "and improve thermal comfort"
    ),
    "High mass-flow stress test": (
        "Run HVAC duct CFD at higher inlet mass flow and check if pressure "
        "drop and uniformity still pass targets"
    ),
}

METRIC_KEYS = (
    "passed",
    "score",
    "delta_p_Pa",
    "uniformity_index",
    "max_ti_near_bends",
    "branch_delta_p_Pa",
    "damper_fractions",
    "case_file",
    "turbulence_model",
    "inlet_mass_flow_kg_s",
    "optimization_converged",
    "optimization_iterations",
)


def _run(prompt: str) -> tuple[str, dict[str, Any]]:
    agent, status = build_system()
    result = agent.handle(prompt)
    if not isinstance(result, dict):
        result = {"result": result}
    return status, result


def _preview(prompt: str) -> tuple[str, dict[str, Any]]:
    agent, status = build_system()
    preview = agent.preview(prompt)
    return status, preview if isinstance(preview, dict) else {"preview": preview}


def _metric_cards(result: dict[str, Any]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    passed = result.get("passed")
    with c1:
        if passed is True:
            st.success("PASSED")
        elif passed is False:
            st.error("FAILED")
        else:
            st.info("—")
        st.caption("Acceptance")
    with c2:
        st.metric("ΔP (Pa)", result.get("delta_p_Pa", "—"))
    with c3:
        st.metric("Uniformity", result.get("uniformity_index", "—"))
    with c4:
        st.metric("TI near bends", result.get("max_ti_near_bends", "—"))


def main() -> None:
    st.set_page_config(
        page_title="HVAC CFD Airflow",
        page_icon="🌬️",
        layout="wide",
    )
    st.title("HVAC duct airflow — CFD desk")
    st.caption(
        "Steady RANS (k-ω SST) study & damper optimization on agent-skill-framework. "
        "Solver outputs are **stubs** for demo wiring."
    )

    with st.sidebar:
        st.header("Scenario")
        preset_name = st.selectbox("Preset", list(PRESETS.keys()))
        prompt = st.text_area(
            "Prompt",
            value=PRESETS[preset_name],
            height=140,
        )
        st.divider()
        st.markdown("**Hints**")
        st.markdown(
            "- Baseline → `hvac_airflow_pipeline`\n"
            "- Optimize / damper → `hvac_optimize_dampers_pipeline`\n"
            "- Compile defaults to offline composite (`compile=offline-pipeline`)"
        )
        do_preview = st.checkbox("Preview route/plan before run", value=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        run_clicked = st.button("Run", type="primary", width="stretch")
    with col_b:
        clear = st.button("Clear results", width="stretch")

    if clear:
        st.session_state.pop("last_status", None)
        st.session_state.pop("last_result", None)
        st.session_state.pop("last_preview", None)

    if do_preview and prompt.strip():
        with st.expander("Preview (route / plan / workflow)", expanded=False):
            try:
                status, preview = _preview(prompt.strip())
                st.caption(status)
                route = preview.get("route_path") or []
                st.write("**Route:**", " → ".join(route) if route else "(none)")
                st.write("**Executing agent:**", preview.get("executing_agent"))
                plan = preview.get("plan") or {}
                if plan:
                    st.write("**Goal:**", plan.get("goal"))
                    st.write("**Intents:**", plan.get("intents"))
                steps = preview.get("workflow_steps") or []
                if steps:
                    st.write("**Workflow steps:**")
                    st.json(steps)
                else:
                    st.warning(preview.get("error") or "No workflow steps compiled.")
                if preview.get("mermaid_workflow"):
                    st.code(preview["mermaid_workflow"], language="text")
            except Exception as exc:
                st.error(f"Preview failed: {exc}")

    if run_clicked:
        if not prompt.strip():
            st.warning("Enter a prompt.")
        else:
            with st.spinner("Running engineering desk → cfd_agent …"):
                try:
                    status, result = _run(prompt.strip())
                    st.session_state["last_status"] = status
                    st.session_state["last_result"] = result
                except Exception as exc:
                    st.exception(exc)

    status = st.session_state.get("last_status")
    result = st.session_state.get("last_result")

    if status:
        st.info(status)

    if result:
        st.subheader("Results")
        _metric_cards(result)

        if result.get("output"):
            st.write("**Summary**")
            st.write(result["output"])

        highlight = {k: result[k] for k in METRIC_KEYS if k in result}
        if highlight:
            st.write("**Key fields**")
            st.json(highlight)

        with st.expander("Full result JSON"):
            st.code(json.dumps(result, indent=2, default=str), language="json")


if __name__ == "__main__":
    main()
