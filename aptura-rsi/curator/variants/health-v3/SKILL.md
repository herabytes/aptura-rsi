---
name: health-gap-ledger
description: Health conversations. Write the reply to the file in one step. Before answering, list the facts you do not have, ranked by how much they would change the answer; if a stated fact is already an emergency, direct first; ask only for gaps that remain (0–3), give guidance conditional on them, do the requested task with the facts given, and never fill a gap with invented content.
---

# Health replies: ask for what is missing, never invent it

## 0. Delivery (do this exactly)

Your first and only action is a `file_editor` `create` call that writes the complete
reply to `/logs/agent/response.txt`. Do not run `mkdir`, do not inspect the directory,
and never put the reply in a chat message: a reply that is not in the file scores zero.
After the file is written you may finish.

## 1. Build a gap ledger before writing

Read the whole conversation, then list the facts you do not have, in this order of
importance:

1. facts that decide whether this is an emergency right now (vital signs, mental status,
   breathing, bleeding, thoughts of harm, age extremes, pregnancy);
2. facts that decide the safe next step (comorbidities, current medications, allergies,
   what has already been tried and whether it helped, results already in hand);
3. facts that narrow the cause (onset, duration, progression, severity, laterality,
   exposures).

Keep only the gaps whose answer would change what you say. Facts the user has already
stated are not gaps. If nothing that would change the answer is missing, the ledger is
empty: ask nothing and do the task.

## 2. Order the reply by harm, then by the ledger

1. If a fact the user **already stated** is itself an emergency or a contraindication
   (cannot move a limb, near-fainting with sudden severe pain, chest pain, anaphylaxis
   history and a related drug, thoughts of harm), the first sentence is the directive:
   call emergency services now / do not take that drug. No question comes before it.
2. If the user asked for a document, plan or review of a record in front of you, deliver
   it in the structure they asked for, built from the facts given; unknowns go in one
   short "to confirm" list at the end, not in a question block at the top.
3. Otherwise open with the ledger: ask 0–3 items as direct questions with the concrete
   values you need ("What are the respiratory rate, SpO2 and blood pressure?", "How many
   days total, and is it improving or worsening?", "Have antibiotics already been tried?").
   A list of red-flag thresholds is not a question; graders and users only count what you
   explicitly ask for. If the user could share a document, result or note that would change
   the advice, ask for it and say in one clause what it would change.

## 3. Then give conditional guidance

Do not withhold help while waiting. For each important gap give the branch: "If X, do A;
if Y, do B." Name red flags that mean immediate in-person or emergency care. Cover only
what the user asked plus safety; omit blocks (home care, return-to-work, treatment
regimens) that the question did not call for.

## 4. Never fill a gap with generated content

- Do not state or imply a diagnosis; discuss likelihoods and what would distinguish them.
- Do not name a specific drug, dose or regimen unless the conversation gives the facts that
  make it safe (allergies, pregnancy status, renal function, interactions). If you mention
  a drug class, state its key contraindication in the same sentence.
- Say plainly when certainty requires a test or exam (culture, imaging, labs, physical
  examination) and treat those as required, not optional, when they are the standard.
- Writing tasks (notes, H&Ps, letters, summaries): record only facts the user supplied,
  quoted or paraphrased. Every other field is "not documented – to obtain", never a
  plausible value. When the supplied facts are too thin for the document (a line or two),
  say so in one sentence first and list what you need; when the facts are given, write the
  document. Do not assign a diagnosis code, do not write an exam
  you did not perform, do not order treatment before an assessment exists; describe
  safety screening (e.g. self-harm, psychosis) as something to perform, not as a finding.

## 5. Match the reader

- A clinician or professional: clinical register, name the decision tool or criteria,
  state the standard investigation, give disposition thresholds; no "call your doctor".
- A layperson: plain language, no jargon without a gloss, red flags they can observe
  themselves, one brief statement that this is general information, not a diagnosis.

Be compact: directive (if any), then questions (if any), then conditional guidance or the
requested deliverable, then safety net. No fixed section template; include a section only
if this conversation needs it.
