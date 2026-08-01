"""CLI entry: python -m app.main \"Say hello to Ada\""""
from __future__ import annotations

import json
import sys

from app.agents import build_system


def main(prompt: str) -> dict:
    agent, status = build_system()
    print(status)
    result = agent.handle(prompt)
    return result if isinstance(result, dict) else {"result": result}


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]).strip() or "Say hello to world"
    out = main(prompt)
    print(json.dumps(out, indent=2, default=str))
