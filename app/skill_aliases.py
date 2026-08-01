"""Map LLM-invented skill names to registered HVAC pipelines."""

SKILL_ALIASES: dict[str, str] = {
    "run_cfd": "hvac_airflow_pipeline",
    "rans_hvac": "hvac_airflow_pipeline",
    "run_rans": "hvac_airflow_pipeline",
    "hvac_cfd": "hvac_airflow_pipeline",
    "airflow_study": "hvac_airflow_pipeline",
    "optimize_airflow": "hvac_optimize_dampers_pipeline",
    "optimize_dampers": "hvac_optimize_dampers_pipeline",
    "balance_ducts": "hvac_optimize_dampers_pipeline",
}
