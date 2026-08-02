"""
Streamlit GUI for HVAC CFD airflow desk.

  pip install -e ".[gui]"
  streamlit run app/gui_app.py
"""
from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from app.agents import build_system

try:
    from agent_skill_framework import (
        list_expandable_from_expansion,
        workflow_mermaid_from_preview,
    )
except ImportError:  # older framework
    list_expandable_from_expansion = None  # type: ignore
    workflow_mermaid_from_preview = None  # type: ignore

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


def _build_dag_mermaid(
    preview: dict[str, Any],
    *,
    expand_all: bool,
    expand_ids: list[str],
    max_depth: int,
) -> str:
    if workflow_mermaid_from_preview is not None:
        return workflow_mermaid_from_preview(
            preview,
            expand_all_composites=expand_all,
            expand_step_ids=expand_ids or None,
            max_depth=max_depth,
        )
    # Fallback: flat mermaid from Agent.preview
    return str(preview.get("mermaid_workflow") or "flowchart TD\n  empty([no diagram])")


def _render_mermaid(diagram: str, *, height: int = 420) -> None:
    """Render Mermaid in the browser; always show source below."""
    if not diagram.strip():
        st.warning("Empty diagram.")
        return

    # Markdown fence (works when Streamlit / browser extension supports it)
    st.markdown(f"```mermaid\n{diagram}\n```")

    # Explicit HTML + Mermaid CDN (reliable local rendering)
    escaped = html.escape(diagram)
    snippet = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "neutral", securityLevel: "loose" }});
  </script>
</head>
<body style="margin:0;padding:8px;background:#fafafa;">
  <pre class="mermaid">{escaped}</pre>
</body>
</html>
"""
    components.html(snippet, height=height, scrolling=True)

    with st.expander("Mermaid source", expanded=False):
        st.code(diagram, language="text")


def _render_workflow_dag(preview: dict[str, Any]) -> None:
    st.subheader("Workflow DAG")
    steps = preview.get("workflow_steps") or []
    if not steps:
        st.warning(preview.get("error") or "No workflow steps — nothing to draw.")
        return

    expand_all = st.checkbox(
        "Expand all composite skills",
        value=True,
        help="Show internal steps of pipelines such as hvac_airflow_pipeline",
        key="dag_expand_all",
    )
    max_depth = st.slider("Composite expand depth", 1, 6, 3, key="dag_depth")

    expand_ids: list[str] = []
    if list_expandable_from_expansion is not None and not expand_all:
        candidates = list_expandable_from_expansion(preview.get("skill_expansion") or [])
        expandable = [c for c in candidates if c.get("expandable")]
        if expandable:
            labels = {
                str(c["id"]): f"{c['id']}: {c.get('skill')} ({c.get('child_count')} children)"
                for c in expandable
            }
            chosen = st.multiselect(
                "Expand selected steps",
                options=list(labels.keys()),
                default=list(labels.keys()),
                format_func=lambda i: labels.get(i, i),
                key="dag_expand_ids",
            )
            expand_ids = list(chosen)

    diagram = _build_dag_mermaid(
        preview,
        expand_all=expand_all,
        expand_ids=expand_ids,
        max_depth=max_depth,
    )
    _render_mermaid(diagram, height=440)

    # Route DAG (agents)
    route_mmd = preview.get("mermaid_route")
    if route_mmd:
        st.markdown("**Agent route**")
        _render_mermaid(str(route_mmd), height=180)


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
            "- Compile defaults to offline composite (`compile=offline-pipeline`)\n"
            "- Use **Preview DAG** before Run to inspect the graph"
        )
        auto_preview = st.checkbox("Auto-refresh preview", value=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        preview_clicked = st.button("Preview DAG", width="stretch")
    with c2:
        run_clicked = st.button("Run", type="primary", width="stretch")
    with c3:
        clear = st.button("Clear", width="stretch")

    if clear:
        for k in ("last_status", "last_result", "last_preview", "last_preview_status"):
            st.session_state.pop(k, None)

    need_preview = preview_clicked or (
        auto_preview and prompt.strip() and "last_preview" not in st.session_state
    )
    # Refresh preview when prompt text changes vs last
    if auto_preview and prompt.strip():
        if st.session_state.get("_preview_prompt") != prompt.strip():
            need_preview = True

    if need_preview and prompt.strip():
        with st.spinner("Compiling preview …"):
            try:
                status, preview = _preview(prompt.strip())
                st.session_state["last_preview_status"] = status
                st.session_state["last_preview"] = preview
                st.session_state["_preview_prompt"] = prompt.strip()
            except Exception as exc:
                st.exception(exc)

    preview = st.session_state.get("last_preview")
    if preview:
        st.caption(st.session_state.get("last_preview_status", ""))
        route = preview.get("route_path") or []
        st.write(
            "**Route:**",
            " → ".join(str(x) for x in route) if route else "(none)",
            " · **Agent:**",
            preview.get("executing_agent"),
        )
        plan = preview.get("plan") or {}
        if plan:
            st.write("**Goal:**", plan.get("goal"))
            intents = plan.get("intents") or []
            if intents:
                st.write("**Intents:**", "; ".join(str(i) for i in intents))

        _render_workflow_dag(preview)

        with st.expander("Workflow steps (JSON)", expanded=False):
            st.json(preview.get("workflow_steps") or [])
        with st.expander("Skill expansion trees", expanded=False):
            st.json(preview.get("skill_expansion") or [])

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
