"""Read-only helpers for the existing Assistant/guided-flow contracts.

The Assistant interprets natural language; these helpers consume its classified
query/intent, verify existing capabilities and produce guidance, never writes.
Rendering/translation uses the user's language in the Assistant entry point.
"""
from dataclasses import dataclass, replace
from pathlib import Path

from system.personalization.advisor import (
    CompositionRecommendation, PersonalizationIntent, recommend,
)
from system.prompts.explorer import PromptQuery, search


@dataclass(frozen=True)
class Guidance:
    level: str
    category: str | None
    message: str
    question: str | None = None
    workflow: str | None = None
    composition: CompositionRecommendation | None = None
    evidence: tuple[str, ...] = ()
    next_action: str | None = None


def guide(root: Path, *, prompt_query: PromptQuery | None = None,
          personalization: PersonalizationIntent | None = None,
          save_requested=False, explain_profile=False) -> Guidance:
    if sum((prompt_query is not None, personalization is not None, bool(explain_profile))) > 1:
        raise ValueError('Classify one material outcome at a time')
    if explain_profile:
        return Guidance('Explain', 'Explain',
                        'A Profile saves a reusable combination of response style and guidance. Nothing is changed.')
    if personalization is not None:
        composition = recommend(root, replace(personalization, reusable=save_requested is True))
        if composition.unavailable:
            return Guidance('Recommend', 'Customize', 'That capability could not be verified.',
                            question='What outcome should the answer help you achieve?', composition=composition)
        if save_requested is True:
            next_action = ('Use the existing saved combination.' if composition.action == 'reuse_profile'
                           else 'Review the smallest reusable change through Profile Builder before saving.')
        else:
            next_action = 'Try this combination for the current task; nothing is saved.'
        return Guidance('Recommend', 'Customize', 'Existing capabilities can provide this response style.',
                        composition=composition, evidence=composition.profiles, next_action=next_action)
    if prompt_query is not None:
        # Executable recommendations always use the owner's active-status gate.
        report = search(root, replace(prompt_query, status='active', limit=1))
        if report.matches:
            match = report.matches[0]
            tags = set(match.tags)
            category = ('Create' if 'creation' in tags else 'Maintain' if 'maintenance' in tags
                        else 'Customize' if 'personalization' in tags
                        else 'Diagnose' if 'diagnostics' in tags else 'Discover')
            return Guidance('Recommend', category, 'An existing workflow matches this goal.',
                            workflow=match.identity, evidence=(match.identity,),
                            next_action='Start this guided workflow with your stated goal.')
        return Guidance('Recommend', 'Discover', 'No usable matching workflow was verified.',
                        question='What result would be most useful? I can recommend a starting point.')
    return Guidance('Recommend', None, 'Start with one useful outcome, such as learning or planning a project.',
                    question='What would you like help with? You can say “I don’t know — recommend one”.',
                    next_action='Describe one current task or ask for a recommendation.')


def improve(root: Path, identities: tuple[str, ...] = ('sot/assistant',)) -> Guidance:
    """Inspect up to three explicitly selected reusable workflows, not Personal facts."""
    if not 1 <= len(identities) <= 3 or len(set(identities)) != len(identities):
        raise ValueError('Select one to three distinct existing workflow identities')
    evidence = []
    unavailable = False
    for identity in identities:
        report = search(root, PromptQuery(identity=identity, limit=1))
        found = bool(report.matches)
        unavailable |= not found
        evidence.append(('available:' if found else 'unavailable:') + identity)
    return Guidance('Recommend', 'Diagnose',
                    'Only the selected reusable workflows were checked; this is not a review of your Personal context.',
                    evidence=tuple(evidence),
                    next_action=('Check the unavailable workflow before proposing a repair.' if unavailable
                                 else 'Try one selected workflow on a useful task; no repair is indicated by these checks.'))
