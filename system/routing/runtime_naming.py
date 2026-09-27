"""Executable ownership for runtime bootstrap and profile identity names."""

from dataclasses import dataclass
import re
from typing import Literal, Optional


CANONICAL_BOOTSTRAP_ACTION = "@do:sot"
LEGACY_BOOTSTRAP_ACTION = "@do:initialSoT"

_CUSTOM_PROFILE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_BUILT_IN_PROFILE_RE = re.compile(r"^g\.[a-z0-9]+(?:\.[a-z0-9]+)*$")


@dataclass(frozen=True)
class BootstrapInvocation:
    action: str
    legacy: bool = False
    diagnostic: Optional[str] = None


def classify_bootstrap_invocation(text: str) -> Optional[BootstrapInvocation]:
    """Resolve an exclusive canonical or legacy bootstrap invocation."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    first = lines[0]
    if first not in (CANONICAL_BOOTSTRAP_ACTION, LEGACY_BOOTSTRAP_ACTION):
        if any(
            first.startswith(f"{action}=") or first.startswith(f"{action} ")
            for action in (CANONICAL_BOOTSTRAP_ACTION, LEGACY_BOOTSTRAP_ACTION)
        ):
            raise ValueError("The bootstrap action accepts no inline payload")
        return None
    if len(lines) != 1:
        raise ValueError("The bootstrap action must be the only prompt content")
    if first == LEGACY_BOOTSTRAP_ACTION:
        return BootstrapInvocation(
            CANONICAL_BOOTSTRAP_ACTION,
            legacy=True,
            diagnostic="@do:initialSoT is deprecated; use @do:sot.",
        )
    return BootstrapInvocation(CANONICAL_BOOTSTRAP_ACTION)


def profile_identity_kind(identity: str) -> Optional[Literal["custom", "built_in"]]:
    """Classify an exact custom or product-owned built-in profile identity."""

    if _BUILT_IN_PROFILE_RE.fullmatch(identity):
        return "built_in"
    if identity.startswith("g.") or identity.startswith("G."):
        return None
    if _CUSTOM_PROFILE_RE.fullmatch(identity):
        return "custom"
    return None


def is_profile_identity(identity: str) -> bool:
    return profile_identity_kind(identity) is not None
