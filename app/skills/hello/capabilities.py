"""Hello capability + pipeline composite."""
from __future__ import annotations

from agent_skill_framework import capability, composite


@capability(
    name="say_hello",
    description="Return a greeting for the given name",
    input_schema={"name": "str"},
    output_schema={"ok": "bool", "message": "str", "output": "str"},
)
def say_hello(input: dict) -> dict:
    name = input.get("name") or "world"
    msg = f"Hello, {name}!"
    return {"ok": True, "message": msg, "output": msg}


composite(
    name="hello_pipeline",
    description="End-to-end hello pipeline",
    steps=["say_hello"],
    input_schema={"name": "str"},
    output_schema={"ok": "bool", "message": "str", "output": "str"},
)
