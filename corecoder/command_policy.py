"""Command authorization policy for the Bash tool."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Literal


PolicyMode = Literal["development", "production"]


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None


DEFAULT_PRODUCTION_ALLOWLIST = {
    "cat",
    "echo",
    "find",
    "git",
    "grep",
    "head",
    "ls",
    "pwd",
    "pytest",
    "python",
    "python3",
    "rg",
    "sed",
    "tail",
    "wc",
}
def evaluate_command(
    command: str,
    mode: PolicyMode = "development",
    allowlist: set[str] | None = None,
) -> PolicyDecision:
    """Decide whether a shell command may run under the selected policy."""
    if mode not in ("development", "production"):
        return PolicyDecision(
            allowed=False,
            reason=f"Unknown command policy mode: {mode}",
        )

    try:
        tokens = shlex.split(command)
    except ValueError:
        return PolicyDecision(
            allowed=False,
            reason="Invalid shell syntax",
        )

    if not tokens:
        return PolicyDecision(
            allowed=False,
            reason="Empty command",
        )
    # Production mode deliberately rejects compound shell expressions.
    # This prevents an allowed command from chaining into a disallowed one.
    if mode == "production" and any(
        marker in command
        for marker in ("&&", "||", "|", ";", "`", "$(", ">", "<")
    ):
        return PolicyDecision(
            allowed=False,
            reason="Compound shell expressions are not allowed in production mode",
        )

    if mode == "development":
        return PolicyDecision(allowed=True)

    command_name = tokens[0]
    permitted = allowlist or DEFAULT_PRODUCTION_ALLOWLIST

    if command_name not in permitted:
        return PolicyDecision(
            allowed=False,
            reason=f"'{command_name}' is not allowed in production mode",

        )

    return PolicyDecision(allowed=True)
