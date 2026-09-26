"""Evidence-backed composition advice over discovered Personalization capabilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from system.personalization.explorer import CapabilityQuery, CapabilityMatch, search


@dataclass(frozen=True)
class PersonalizationIntent:
    formats: tuple[str, ...] = ()
    tone: str | None = None
    depth: str | None = None
    controls: tuple[tuple[str, str], ...] = ()
    behaviors: tuple[str, ...] = ()
    reusable: bool = False


@dataclass(frozen=True)
class CompositionRecommendation:
    action: str
    profiles: tuple[str, ...]
    formats: tuple[str, ...]
    tone: str | None
    depth: str | None
    controls: tuple[tuple[str, str], ...]
    behaviors: tuple[str, ...]
    unavailable: tuple[str, ...]
    profile_creation_eligible: bool


def _exact(root: Path, lane: str, identity: str) -> CapabilityMatch | None:
    report = search(root, CapabilityQuery(identity=identity, lanes=(lane,), limit=1))
    return report.matches[0] if report.matches else None


def _profile_terms(match: CapabilityMatch) -> set[str]:
    return set(match.components)


def recommend(root: Path, intent: PersonalizationIntent) -> CompositionRecommendation:
    unavailable = []
    for lane, identities in (
        ("format", intent.formats),
        ("tone", (intent.tone,) if intent.tone else ()),
        ("depth", (intent.depth,) if intent.depth else ()),
        ("behavior", intent.behaviors),
    ):
        for identity in identities:
            if _exact(root, lane, identity) is None:
                unavailable.append(f"{lane}:{identity}")
    for identity, value in intent.controls:
        match = _exact(root, "control", identity)
        if match is None or value not in match.allowed_values:
            unavailable.append(f"control:{identity}={value}")
    if unavailable:
        return CompositionRecommendation(
            "unavailable",
            (),
            intent.formats,
            intent.tone,
            intent.depth,
            intent.controls,
            intent.behaviors,
            tuple(unavailable),
            False,
        )

    profiles: tuple[str, ...] = ()
    if intent.behaviors:
        required = {
            *(f"behavior:{value}" for value in intent.behaviors),
            *(f"format:{value}" for value in intent.formats),
        }
        if intent.tone:
            required.add(f"tone:{intent.tone}")
        if intent.depth:
            required.add(f"depth:{intent.depth}")
        candidates = search(root, CapabilityQuery(lanes=("profile",), limit=10)).matches
        suitable = [match for match in candidates if required.issubset(_profile_terms(match))]
        if suitable:
            selected = min(
                suitable,
                key=lambda match: (len(_profile_terms(match) - required), match.identity),
            )
            profiles = (selected.identity,)

    direct_count = len(intent.formats) + bool(intent.tone) + bool(intent.depth) + len(intent.controls)
    creation_eligible = intent.reusable and not profiles and direct_count + len(intent.behaviors) >= 2
    action = "reuse_profile" if profiles and not intent.controls else "compose"
    return CompositionRecommendation(
        action,
        profiles,
        intent.formats,
        intent.tone,
        intent.depth,
        intent.controls,
        intent.behaviors,
        (),
        creation_eligible,
    )
