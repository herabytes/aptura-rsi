# Curator Knowledge Corpus

Purpose: give the hackathon curator a compact, cross-domain theory of how to improve a fixed learner from limited feedback. This is intended as a **research/diagnosis guide**, not as a list of medical or task-specific fixes.

## Core idea

Treat improvement as an iterative scientific/coach-like process:

**observe -> diagnose -> form competing hypotheses -> choose a high-value intervention/experiment -> predict what should change -> run -> compare -> update the diagnosis**

Do not assume that the most visible rubric failure is the underlying capability deficit. Prefer explanations that account for multiple failures and interventions that are small enough to make the result interpretable.

---

## 1. Value of information (VOI)

When information is missing, ask:

> Which missing fact would most change the decision or next action?

Do not collect information just because it is available or because it appears on a generic checklist. Prioritize information that can change the recommended action, distinguish competing hypotheses, or substantially reduce consequential uncertainty.

Operational rule for the curator:

- For each uncertainty, estimate whether resolving it would change the intervention.
- Prefer high-impact, low-cost information.
- When choosing another trajectory/task to inspect, prefer one that is likely to distinguish between competing explanations.
- Think of each extra eval as having a cost; spend it where it has the highest expected information or performance value.

Why relevant: value-of-information analysis explicitly treats additional information as something to prioritize according to its expected decision benefit, and optimal experimental design formalizes choosing data/experiments under cost and uncertainty.

---

## 2. Scientific hypothesis testing

A useful improvement process is not “find a plausible fix”; it is:

**observation -> hypothesis -> prediction -> controlled test -> evidence -> belief update**

For every proposed intervention, the curator should state:

1. What mechanism it is supposed to change.
2. What observable behaviour should improve if that mechanism is correct.
3. What result would weaken or falsify the hypothesis.
4. What collateral regression is possible.

Prefer interventions that make competing explanations distinguishable.

---

## 3. Deliberate practice

Expert improvement is associated with repeated practice focused on particular tasks, immediate feedback, evaluation, and opportunities to refine behaviour.

Translate this into learner improvement:

- isolate a concrete weakness;
- give a targeted behavioural procedure;
- test it repeatedly;
- use feedback to refine the procedure;
- avoid treating a broad score as enough information to diagnose the mechanism.

The implication is that “practice + feedback + targeted correction” is more informative than repeatedly asking for a better overall answer.

---

## 4. Formative feedback and coaching

Educational feedback research emphasizes that feedback is not uniformly useful: its information content and focus matter. Process-oriented, actionable feedback is generally more useful than bare correctness/score feedback. Research on instructional coaching also emphasizes active learning, practice opportunities, feedback, sustained work, and coherence.

For curator reasoning:

- Convert verdicts into information about **what the learner did**, not just whether it was right.
- Prefer feedback that points toward a change in process/strategy.
- Separate “the output was wrong” from “here is the behaviour that caused it to be wrong.”
- After an intervention, explicitly check whether the targeted behaviour changed.

---

## 5. Root-cause and causal diagnosis

A repeated error is a symptom, not necessarily a capability.

When multiple failures look similar, ask:

> What common mechanism could generate all of these observations?

But also consider the opposite possibility:

> Are these genuinely independent failures that only look similar because the rubric language is similar?

Use a small causal hypothesis tree rather than immediately collapsing everything into one explanation.

Useful distinction:

**knowledge failure** — does not have/recall the relevant information

**representation failure** — misreads what the task is asking / fails to construct the relevant state

**planning/procedure failure** — knows the pieces but executes them in the wrong order

**tool-use failure** — has access to an appropriate capability but fails to use it

**verification failure** — produces an answer without checking a critical property

**communication failure** — reasoning may be adequate but the response fails the task/rubric

This decomposition is a heuristic, not a required taxonomy.

---

## 6. Minimal, interpretable interventions

When testing an intervention, prefer the smallest change that could plausibly test the hypothesis.

Why:

If a huge skill rewrite improves performance, you learn very little about which mechanism mattered.

A good intervention should therefore have a statement like:

> “We believe X is causing Y. We changed Z because Z specifically targets X. If X is the cause, Y should improve while unrelated behaviours remain roughly stable.”

This is especially important when evaluation is expensive.

---

## 7. Generalization and transfer

Do not confuse “fixed the examples I inspected” with “improved the capability.”

After an intervention, compare:

- previously failed tasks;
- fresh tasks with similar structure;
- fresh tasks from different surface forms/domains when available.

A strong intervention should explain why it transfers rather than merely matching observed rubric wording.

Ask:

> What abstract procedure did the learner acquire that could apply beyond these examples?

---

## 8. Learning from the intervention itself

The intervention is also an experiment about the learner.

After each run, ask:

**Fixed:** Which predicted behaviours improved?

**Unchanged:** Which predicted failures persisted?

**Regressed:** What got worse?

**Unexpected:** What changed that was not predicted?

**New frontier:** Once the old bottleneck moves, what is now the highest-impact remaining limitation?

This turns the process into sequential model-building rather than a succession of prompt edits.

---

## 9. LLM self-refinement / verbal reinforcement

Work such as Self-Refine and Reflexion shows that language-model agents can improve behaviour using natural-language feedback or reflections without updating model weights. This supports the general idea that feedback can function as a temporary behavioural memory/procedure.

But this should **not** be taken to mean that self-generated explanations are automatically correct. External grader signals and controlled experiments are valuable precisely because the model can produce plausible but wrong causal stories about its own failures.

For the curator:

> Treat explanations as hypotheses to test, not ground truth.

---

## Curator operating principles

1. **Diagnose before prescribing.**
2. **Look for mechanisms, not rubric phrases.**
3. **Prefer explanations that unify multiple observations, but do not force unification.**
4. **Use value-of-information thinking when deciding what to inspect or test next.**
5. **Every intervention should have an explicit predicted mechanism.**
6. **Prefer minimal interventions when they make causal interpretation cleaner.**
7. **Use external evaluation to falsify plausible stories.**
8. **Measure transfer, not just repair on training examples.**
9. **Track regressions and newly exposed bottlenecks.**
10. **Treat each experiment as evidence about the learner, not merely as a chance to raise the score.**

## Suggested curator output for each iteration

### Diagnosis
- top failure modes
- evidence / representative trajectories
- competing root-cause hypotheses

### Intervention proposals
For each candidate:
- mechanism targeted
- exact change to SKILL.md / data / tool
- expected effect
- possible regressions
- what result would falsify the hypothesis
- expected generalization

### Experiment choice
Rank candidates by:

**expected performance gain × generality × information gained / evaluation cost**

This is a heuristic, not a literal calibrated equation.

### After the run
- predicted vs observed effects
- fixed / unchanged / regressed behaviours
- updated causal hypotheses
- next experiment

---

## Source reading

- Jackson, Baio, Heath et al. (2022), *Value of Information Analysis in Models to Inform Health Policy*, Annual Review of Statistics and Its Application. Useful overview of VOI as prioritizing additional information according to decision benefit.
- Chaloner & Verdinelli (1995) / modern survey: *Optimal Experimental Design: Formulations and Computations*. Experimental design as choosing informative data/experiments under explicit objectives and cost.
- Ericsson (2008), *Deliberate Practice and Acquisition of Expert Performance: A General Overview*, Academic Emergency Medicine. Focused practice, immediate feedback, evaluation, and repeated refinement.
- Wisniewski, Zierer & Hattie (2020), *The Power of Feedback Revisited: A Meta-Analysis of Educational Feedback Research*. Feedback effects vary substantially with information content and form.
- Brummer et al. (2024), *A meta-analysis of the effects of context, content, and task factors of digitally delivered instructional feedback on learning performance*. Feedback focus/content and learner/task factors help explain heterogeneous effects.
- Desimone & Pak (2017), *Instructional Coaching as High-Quality Professional Development*. Coaching framework emphasizing content focus, active learning, sustained duration, coherence, and participation.
- Madaan et al. (2023), *Self-Refine: Iterative Refinement with Self-Feedback*. Iterative feedback/refinement can improve LLM outputs across tasks.
- Shinn et al. (2023), *Reflexion: Language Agents with Verbal Reinforcement Learning*. Language feedback/reflection can improve agent behaviour without weight updates.
- The scientific-method principle used here is the hypothetico-deductive loop: observations -> hypotheses -> controlled tests -> updated conclusions.

## Important limitation

This corpus is a compact synthesis for guiding a hackathon curator. It is **not** a claim that these fields have a single unified theory of AI self-improvement, nor that any one principle is guaranteed to improve the frozen learner. The value is as a menu of hypotheses and experimental habits.
