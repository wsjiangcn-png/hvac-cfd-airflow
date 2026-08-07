"""Hard trial license gate — same mechanism as Bracket FEA."""
from __future__ import annotations

from agent_skill_framework import (
    LicenseInfo,
    TrialLicenseError,
    license_banner,
    validate_license,
)

REQUIRED_EDITION = "hvac-cfd"


def require_license(license_key: str | None = None) -> LicenseInfo:
    """Validate AFIPER1 key for this product; raise TrialLicenseError on failure."""
    info = validate_license(license_key, required_edition=REQUIRED_EDITION)
    print(license_banner(info))
    return info


def exit_on_license_error() -> LicenseInfo:
    try:
        return require_license()
    except TrialLicenseError as err:
        raise SystemExit(
            f"LICENSE ERROR: {err}\n"
            "Place your key in license.key or set AGENT_SKILL_LICENSE_KEY."
        ) from err
