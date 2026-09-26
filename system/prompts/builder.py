"""Reuse-before-create decisions for the client-neutral Prompt Builder."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReuseAssessment:
    exact_identity: str | None = None
    parameterized_identity: str | None = None
    composition: tuple[str, ...] = ()
    edit_identity: str | None = None
    same_semantic_owner: bool = False


def choose_action(assessment: ReuseAssessment) -> tuple[str, str | None]:
    if assessment.exact_identity:
        return "reuse_exact", assessment.exact_identity
    if assessment.parameterized_identity:
        return "reuse_parameterized", assessment.parameterized_identity
    if assessment.composition:
        return "compose", None
    if assessment.edit_identity and assessment.same_semantic_owner:
        return "edit", assessment.edit_identity
    return "create", None
