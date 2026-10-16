# Change log

This user-facing log records **dated changes to the public Personal-SoT product**, explaining what changed, why it matters, and how people can use it.

Entries are listed newest first. For future user-visible features, behavior changes, significant fixes, and removals, add a dated entry with **What**, **Why**, and **How to use / migrate**. Keep entries tied to actual accepted changes, not proposed work or assumptions. Earlier releases are not reconstructed here without verified evidence.

## 2026-10-16 — Improved: Private user-owned workspace updates

**What changed**
- Verified private user-owned Context content, Prompt templates, custom Profiles,
  and eligible user-owned Presentation content may be saved directly to private
  `main` after a complete preview, confirmation, current-state checks, and
  focused validation appropriate to the changed owner.
- Routine user-owned content changes no longer require a temporary branch,
  merge, full Python unit suite, or unrelated repository-wide validators.
- Prompt and Profile Builders use focused target checks after writes while
  retaining preflight, ownership, dependencies, and concurrency protections.
  Structural context/access changes retain their targeted checks.
- Private adapter, governance, product-shipped module, and public product
  changes remain under their protected development workflows.

**Why**
- Remove unnecessary friction for personal content maintenance, including
  authorized web-based AI clients, without weakening product/privacy boundaries.

**How to use**
Ask your connected Personal SoT Assistant to update personal project content
or to create/edit a custom Prompt/Profile. Review the full preview and confirm.
With real write permission and established focused checks, the change goes
directly to private `main`. Otherwise, the Assistant explains the blocker
instead of claiming validation or a commit succeeded.

**Compatibility:** Public product changes continue through governed
branch/CI/release. Existing private installations must import the released
public code using normal Safe Update and reconcile their private Branch Flow.

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
