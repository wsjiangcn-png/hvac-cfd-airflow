"""CLI entry: python -m app.main \"Run RANS on HVAC ducts\""""
from __future__ import annotations

import json
import sys

from app.agents import build_system

DEFAULT_PROMPT = (
    "Run steady RANS k-ω SST on the multi-branch HVAC duct network "
    "and report pressure drop and diffuser uniformity"
)


def main(prompt: str) -> dict:
    agent, status = build_system()
    print(status)
    result = agent.handle(prompt)
    return result if isinstance(result, dict) else {"result": result}


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]).strip() or DEFAULT_PROMPT
    out = main(prompt)
    print(json.dumps(out, indent=2, default=str))
