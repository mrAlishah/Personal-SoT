# AI Decision Council

The AI Decision Council helps you compare important choices without having to design a questionnaire or know which specialists to consult. It is a reusable Prompt; its specialists are **simulated AI perspectives**, not separately verified human professionals or independently running agents.

## Start a decision

In an AI client connected to your authorized Personal-SoT, ask in everyday language:

```text
Find and run the AI Decision Council for this decision:
Should I change jobs or remain in my current position?
```

Or use the exact Prompt command:

```text
@run:decision/council

Should I change jobs or remain in my current position?
```

You can write the decision in your own language. To add a permitted, relevant context scope, an advanced user may place `@ctx:<scope>` in the same leading control block, but the prompt does not grant access to private information by itself.

## What happens next?

The Council adapts the depth of review to your own risk rating (1–5), urgency, uncertainty, and potential consequences. It follows nine steps:

1. **Clarify your real decision.** It restates your problem in plain language and asks you to approve or correct it *before* council analysis starts.
2. **Assess risks.** You choose a risk score from 1 to 5; the Council explains the relevant risk areas and flags urgent deadlines.
3. **Confirm your priorities — always.** Review what matters most to you, such as cost, safety, time, autonomy, or preserving a relationship. You may correct the priorities.
4. **Choose specialist perspectives.** Usually two to four relevant AI roles explain how they can help.
5. **Ask only decisive questions and research gaps.** Questions identify the specialist and explain why the answer matters. The Council should research answerable facts using authorized, available sources instead of repeatedly asking you.
6. **Discuss and challenge findings.** Perspectives scrutinize assumptions, disagree when justified, and identify missing evidence.
7. **Preview the decision brief.** Check the problem, priorities, important Q&A, evidence, unknowns, and specialist opinions. Correct or approve this summary.
8. **Compare options and outcomes.** The Council usually provides three *meaningfully different* paths, with trade-offs, risks, costs, and realistic scenarios; it does not invent an option to fill a quota.
9. **Recommend next steps.** It explains the best-supported path for your priorities, the strongest counterargument, what could change the recommendation, and the next practical action.

Progress appears throughout the session, but the number of questions is not fixed.

## Answering questions

You can respond in your own words, including:

- **“I don't know.”** The Council can research when it has an authorized source or keep the fact explicitly unknown.
- **“My answer is different: ...”** You never have to accept a suggested option.
- **“Skip this question” / “Stop questions from this specialist.”** The Council should continue using the remaining evidence and flag limitations.
- **“Correct my earlier answer: ...”** Relevant assumptions and conclusions should be reconsidered.
- **“Summarize with what we know.”** Skip further low-value questions and obtain a provisional recommendation with explicit uncertainty.

When your client offers interactive choices, use them if helpful; if not, write a normal text reply. There is no need for a special interface.

## Understanding the final answer

Expect a short summary first, followed by a comparison of options and a more detailed explanation when needed. A good decision brief distinguishes:

| Kind of information | What it means |
|---|---|
| Confirmed fact | Grounded in the accessible evidence or your confirmed information |
| Assumption | A condition used for analysis but not yet established |
| Unknown | Something important the Council cannot reliably determine |
| Estimate | A calculation with explicit inputs and limitations |
| Recommendation | Advice based on your confirmed priorities, not a final decision made for you |

The Council **does not invent percentages for success, financial return, or legal outcomes**. Numerical probabilities require credible data or an explicitly defensible model; otherwise it compares scenarios qualitatively. For legal, medical, financial, or other high-stakes decisions, qualified human review may still be necessary.

## Privacy and availability

The Council does not automatically send messages, make purchases, take external actions, or save a decision into your SoT. Any real action or durable change needs applicable permission and confirmation.

Your private context stays in your private `sot`; never copy Personal case details into the public product. If `decision/council` is not found, first [update your private SoT](update.md), check [prompt discovery](find_and_use_prompts.md), and verify that your AI client can actually access the selected repository.

See [Beginner guide](readme.md) and [changes and features](../../change_log.md).
