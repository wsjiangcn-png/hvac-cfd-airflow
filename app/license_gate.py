"""Hard trial license gate (SkillDesk standard).

Never construct LicenseInfo directly — it is sealed in agent-skill-framework.
Always use validate_license().

Dev-only: SKILLDESK_SMOKE=1 skips the hard gate (returns None).
"""
from __future__ import annotations

import os

from agent_skill_framework import (
    LicenseInfo,
    TrialLicenseError,
    license_banner,
    validate_license,
)

REQUIRED_EDITION = "hvac-cfd"


def require_license(license_key: str | None = None) -> LicenseInfo:
    info = validate_license(license_key, required_edition=REQUIRED_EDITION)
    print(license_banner(info))
    return info


def exit_on_license_error() -> LicenseInfo | None:
    if os.environ.get("SKILLDESK_SMOKE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        print("LICENSE: SKILLDESK_SMOKE=1 — gate skipped (dev only)")
        return None
    try:
        return require_license()
    except TrialLicenseError as err:
        raise SystemExit(
            f"LICENSE ERROR: {err}\n"
            "Place your key in license.key or set AGENT_SKILL_LICENSE_KEY.\n"
            "Or set SKILLDESK_SMOKE=1 for local UI/CLI smoke only."
        ) from err
