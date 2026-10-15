# Change log

This user-facing log records **dated changes to the public Personal-SoT product**, explaining what changed, why it matters, and how people can use it.

Entries are listed newest first. For future user-visible features, behavior changes, significant fixes, and removals, add a dated entry with **What**, **Why**, and **How to use / migrate**. Keep entries tied to actual accepted changes, not proposed work or assumptions. Earlier releases are not reconstructed here without verified evidence.

## 2026-10-15 — Added: Adaptive AI Decision Council (MVP)

**What changed**
- Added the reusable `decision/council` Prompt with a nine-stage decision workflow: clarify and confirm the problem; rate risks; confirm personal priorities; select specialist perspectives; ask high-impact questions or research answers; compare independent AI viewpoints; review an evidence/assumption preview; compare viable options; and recommend actions.
- Question depth adapts to the user-rated risk, urgency, uncertainty, and cost of error. Users can correct answers, skip low-value questions, stop one specialist's questions, or request an early summary.
- Added an introductory [Decision Council user guide](guides/user/decision_council.md) and navigation links for beginners.

**Why**
- To help users reach a clearer, better-supported decision without long repetitive questionnaires.
- To distinguish verified facts from assumptions and avoid invented numerical probabilities or a false claim of independent human experts.

**How to use**

```text
@run:decision/council

Should I accept a new job offer or stay where I am?
```

Or ask the Personal SoT Assistant to find and run the Council. Read the [guide](guides/user/decision_council.md) for the stages, response options, limitations, and privacy notes.

**Compatibility:** The public version uses existing `eli5` and `compare` formats; it does not depend on a Personal-only `decision/support` Profile. It does not change existing user context or save decisions automatically.
