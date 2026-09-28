# Beginner Guidance conversational acceptance

Date: 2026-09-28

## Evidence boundary

This was a live rendered evaluation in ChatGPT Web with controlled public
capability evidence from this branch. The client produced real model responses,
but it was not connected to the branch's local Python runtime or an authorized
repository writer. It therefore did not execute `guidance.py`, Profile Builder,
or local validators. The exact selected model label was not exposed in the
captured UI.

This is conversational evidence, not a claim of full installed-client
integration. Executable tests separately cover deterministic routing effects,
real Profile preview/confirmation/write/validation, and no-write result flags.

The first batched screening response mixed language between nominally
independent scenarios and described an unavailable behavior as transiently
usable. Those observations were treated as possible batch contamination, not
accepted evidence. Fresh standalone conversations then verified the behavior
limitation and bounded improvement paths correctly. No material reproducible
defect remained.

## Results

| Scenario | Route | Action level | Questions | Evidence used | Mutation claim | Validation claim | Next action | Beginner language quality |
|---|---|---|---:|---|---|---|---|---|
| Empty English request | General guidance | Recommend | 1 | Two ordinary outcome examples | None | None | State one useful outcome | Clear English; no menu or internal terms |
| Persian uncertainty | Create/project guidance | Recommend | 1 | Verified guided project starting point | None | None | Choose learning or another concrete outcome | Natural Persian; no category or directive request |
| Persian answers-too-long | Customize/depth | Recommend/trial | 0 | Verified short response capability | Explicitly transient only | None | Try shorter answers in the current interaction | Natural Persian; no Profile creation |
| Persian Profile explanation | Explain | Explain | 0 | Profile purpose and examples | Explicitly none | None | None required | Plain Persian; no implicit save |
| Persian learning project | Create/project | Recommend | 1 | Verified active project workflow | None | None | State the learning topic | Natural Persian; no path or prompt identity |
| English save-style request | Customize/Profile | Preview | 0 | No exact Profile; Advisor eligibility for short + professional | Explicitly preview only; nothing written | Explicitly not run | Confirm, then use a write-capable client | Clear English and clear Preview/Apply boundary |
| Behavior without usable Profile | Customize limitation | Recommend | 1 | Behavior exists; no usable Profile or direct behavior composition | Explicitly none | None | Clarify the desired planning outcome | Natural beginner language; no false trial claim |
| Persian Improve my SoT | Bounded Diagnose/Recommend | Recommend | 0 | Verified Assistant entrypoint only | Explicitly none; no repair | Explicitly not run | Try one natural-language request through the Assistant | Natural Persian; coverage and no Personal sweep stated |
| English confirmed Apply on no-write client | Customize/Profile | Apply blocked | 0 | Prior confirmed Preview plus actual client capability | Explicitly not applied | No validation claimed; validation belongs after a real write | Apply from a write-capable client | Clear English capability limitation |
| Persian deep professional research | Customize/Profile reuse | Recommend/reuse | 1 | Verified exact existing research Profile | None | None | Supply the research topic | Natural Persian; reuse before create |

## Acceptance conclusion

The live rendered responses preserved one beginner entry point, automatic
routing, one-question guidance, reuse-before-create, transient trials, bounded
improvement, and truthful no-write behavior in both English and Persian.

The no-write live session could describe a complete beginner-facing proposal
but could not generate or apply a repository-backed canonical diff. That
boundary was reported rather than presented as completed work. The executable
Profile Builder integration remains the evidence for complete diff, stale-state
checks, authorized write, and real validation.

ChatGPT also rendered citations from the legacy project source set. Their
labels are client UI, not Assistant output from this branch, so they were not
treated as evidence of public-client progressive disclosure. A full deployment
test should revisit citation presentation after the public repository is the
actual connected source.
