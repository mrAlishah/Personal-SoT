"""Executable ownership for runtime system-action, prompt-action, and
profile identity names; see system/routing/switch_syntax.md."""

from dataclasses import dataclass
import re
from typing import Literal, Optional


CANONICAL_BOOTSTRAP_ACTION = "@do:sot"
LEGACY_BOOTSTRAP_ACTION = "@do:initialSoT"
HELP_ACTION = "@do:help"
ASSIST_ACTION = "@do:assist"

RUN_ACTION = "@run"
EDIT_ACTION = "@edit"
DELETE_ACTION = "@delete"

_SYSTEM_ACTIONS = (CANONICAL_BOOTSTRAP_ACTION, LEGACY_BOOTSTRAP_ACTION, HELP_ACTION, ASSIST_ACTION)
_BODILESS_SYSTEM_ACTIONS = (CANONICAL_BOOTSTRAP_ACTION, LEGACY_BOOTSTRAP_ACTION)
_PROMPT_ACTION_KEYWORDS = (RUN_ACTION, EDIT_ACTION, DELETE_ACTION)

_CUSTOM_PROFILE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_BUILT_IN_PROFILE_RE = re.compile(r"^g\.[a-z0-9]+(?:\.[a-z0-9]+)*$")

_PATH_SEGMENT = r"[a-z0-9]+(?:_[a-z0-9]+)*"
_PROMPT_PATH_RE = re.compile(rf"^{_PATH_SEGMENT}(?:/{_PATH_SEGMENT})*$")
_PHYSICAL_PROMPT_PREFIX = "workspace/prompts/"


@dataclass(frozen=True)
class BootstrapInvocation:
    action: str
    legacy: bool = False
    diagnostic: Optional[str] = None


@dataclass(frozen=True)
class SystemActionInvocation:
    action: str
    legacy: bool = False
    diagnostic: Optional[str] = None
    body: str = ""


@dataclass(frozen=True)
class PromptActionInvocation:
    keyword: str
    prompt_id: str


def _leading_control_block(text: str) -> tuple[list[str], str]:
    """Non-blank leading lines (the control block) and the raw body after
    the first blank line, per switch_syntax.md's control-block/body split.
    """
    lines = text.splitlines()
    control: list[str] = []
    index = 0
    while index < len(lines) and lines[index].strip():
        control.append(lines[index].strip())
        index += 1
    if index < len(lines) and not lines[index].strip():
        index += 1
    body = "\n".join(lines[index:]).strip()
    return control, body


def classify_system_action(text: str) -> Optional[SystemActionInvocation]:
    """Resolve an exclusive canonical or legacy system action.

    The control block is searched as a whole, not only its first line, so
    a preceding selector/control/prompt-action/recap directive cannot make
    a real system action invisible. `@do:sot` (and its legacy
    `@do:initialSoT` alias) is bodiless and exclusive: no body, no
    `@param`, no companion directive of any kind. `@do:help` and
    `@do:assist` may carry an ordinary body after the control block but
    still reject every companion directive and a second high-level
    action, since the control block they occupy must contain only the one
    action line — this is enforced by a control-block line count, so it
    holds regardless of where the action line sits within it.
    """
    control, body = _leading_control_block(text)
    if not control:
        return None
    exact_matches = [line for line in control if line in _SYSTEM_ACTIONS]
    if not exact_matches:
        if any(line.startswith(f"{action}=") or line.startswith(f"{action} ")
               for line in control for action in _SYSTEM_ACTIONS):
            raise ValueError("A system action accepts no inline payload")
        return None
    if len(exact_matches) > 1:
        raise ValueError("At most one system action may appear in one control block")
    first = exact_matches[0]
    legacy = first == LEGACY_BOOTSTRAP_ACTION
    canonical = CANONICAL_BOOTSTRAP_ACTION if legacy else first
    if canonical in _BODILESS_SYSTEM_ACTIONS:
        if len(control) != 1 or body:
            raise ValueError("The bootstrap action must be the only prompt content")
        body = ""
    elif len(control) != 1:
        raise ValueError(f"{canonical} accepts no companion directive")
    diagnostic = "@do:initialSoT is deprecated; use @do:sot." if legacy else None
    return SystemActionInvocation(canonical, legacy=legacy, diagnostic=diagnostic, body=body)


def classify_bootstrap_invocation(text: str) -> Optional[BootstrapInvocation]:
    """Backward-compatible bootstrap-only view; see `classify_system_action`.

    Existing callers (e.g. `system/connectors/source.py`) resolve only
    `@do:sot`/`@do:initialSoT` through this name; `@do:help`/`@do:assist`
    correctly resolve to `None` here even though `classify_system_action`
    recognizes them, since they are not bootstrap/re-anchor invocations.
    """
    result = classify_system_action(text)
    if result is None or result.action != CANONICAL_BOOTSTRAP_ACTION:
        return None
    return BootstrapInvocation(result.action, legacy=result.legacy, diagnostic=result.diagnostic)


def classify_prompt_action(text: str) -> Optional[PromptActionInvocation]:
    """Resolve an exact `@run`/`@edit`/`@delete` prompt-action invocation.

    Prompt identity resolves exactly to `workspace/prompts/<prompt_id>.md`;
    this validates only the identity's own grammar (lowercase snake_case
    `/`-hierarchical segments), never a fuzzy match or a corrected
    spelling. The legacy `@do:prompt:`/`@edit:prompt:`/`@delete:prompt:`/
    `@confirm:delete:prompt:` spellings and bare `@prompt:` do not match
    any recognized keyword here and resolve to `None` (unresolved), never
    normalized. A recognized keyword with a malformed path (including a
    `workspace/prompts/` physical prefix or a traversal segment) raises
    rather than silently guessing. A system action or `@recap` elsewhere
    in the same control block is a second high-level action and is
    rejected regardless of which one comes first.
    """
    control, _body = _leading_control_block(text)
    matches: list[tuple[str, str]] = []
    for line in control:
        for keyword in _PROMPT_ACTION_KEYWORDS:
            prefix = f"{keyword}:"
            if line.startswith(prefix):
                matches.append((keyword, line[len(prefix):]))
                break
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError("At most one prompt action may appear in one control block")
    if any(line in _SYSTEM_ACTIONS or line.startswith("@recap:") for line in control):
        raise ValueError("A prompt action cannot coexist with a system action or recap")
    keyword, candidate = matches[0]
    if candidate.startswith(_PHYSICAL_PROMPT_PREFIX) or candidate == "workspace":
        raise ValueError(f"{keyword} takes a prompt identity, not the physical prefix")
    if not _PROMPT_PATH_RE.fullmatch(candidate):
        raise ValueError(f"{keyword} requires an exact lowercase_snake_case prompt path")
    return PromptActionInvocation(keyword, candidate)


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
