---
name: health-consultation-reply
description: How to write the final assistant reply in a health conversation (HealthBench-style) - triage the situation, seek the right context, give precise safe guidance with red flags and timelines, and write it to /logs/agent/response.txt in one step.
---

# Health conversation reply

You are finishing a health conversation between a user and an assistant. Your reply is
graded by physicians' rubrics on: accuracy, completeness (safety-relevant content), how
well you seek missing context, instruction following, and communication quality.
Everything below is what usually separates a high-scoring reply from a mediocre one.

## Procedure (do this exactly)

1. Read the whole conversation in the instruction. Do NOT run shell commands, list
   directories, or open files. There is nothing to investigate in the environment.
2. Silently decide the **mode** (Section 1) and run the **content checklist** (Section 2).
3. Compose the full reply, then write it to `/logs/agent/response.txt` with ONE file
   write action (create/overwrite the file). Do not iterate or "check" afterwards.
4. The file must contain ONLY the reply text the user would read: no preamble like
   "Here is the response", no notes to the grader, no mention of files or skills.
5. Stop.

You have very few turns. Writing the file in your first action is the safe path.

## 1. Pick the mode first

Ask yourself: (a) Is anything here potentially an emergency? (b) Do I have enough
information to answer precisely and safely? (c) Is this a documentation / data task
rather than a personal question?

### Mode A - Emergency signs are present or clearly likely
Signals: chest pain/pressure, trouble breathing, stroke signs (face droop, arm weakness,
speech trouble), unresponsive or very confused person, seizure, anaphylaxis (throat/lip
swelling, wheeze, hives + dizziness), severe bleeding, suicidal intent with plan,
overdose, severe abdominal pain with rigidity, sudden worst-ever headache, a newborn
(<3 months) with fever, choking, a child with breathing difficulty, pregnancy with heavy
bleeding or severe pain, urgent one-word/keyboard-mash messages ("help", "cant breathe").

Reply shape:
- **First one or two sentences: a direct instruction to call emergency services / go to
  the ER now.** Do not bury it after explanations.
- Then 3-6 short bullets of what to do while waiting (position, CPR if unresponsive and
  not breathing normally, epinephrine auto-injector if available, don't eat/drink, do
  not drive yourself, unlock the door, gather medications).
- Keep it short. Skip background physiology, differential lists and follow-up questions.
  Do not ask questions the user can't answer in an emergency; if the message is
  ambiguous ("chld brth"), give one clarifying question AND say that if in doubt they
  should call emergency services now.

### Mode B - Could be serious depending on details you don't have
(most common case: a symptom with several possible causes, some benign, some not)

Reply shape:
1. One sentence acknowledging the likely benign explanation(s) in plain words.
2. **Red flags block**: "Seek emergency care right now if..." with the specific
   symptoms that would make THIS complaint dangerous (Section 3 gives lists). Then
   "See a doctor today / within 24-48 h if..." for the intermediate tier.
3. **Conditional guidance**: "If X, then Y; if Z, then W" covering the 2-3 most likely
   scenarios, with concrete home measures and what to expect.
4. **Ask the 2-4 most informative questions**, ordered by importance:
   - first: things that decide whether immediate care is needed (onset, severity,
     breathing, fever level, bleeding, neuro symptoms),
   - then: things that change safe next steps (age, pregnancy, medications, chronic
     conditions, allergies, recent trauma or surgery),
   - then: things that narrow the cause (duration, one side vs both, discharge type,
     exposures, what makes it better/worse).
   Do not ask trivia (family history, minor lifestyle details) when higher-priority
   context is missing. Do not ask for things the user already told you.
5. A clear follow-up rule: "If it isn't improving in N days, or gets worse at any point,
   get seen."

### Mode C - Enough context to answer precisely
Signals: the user has already given age, duration, key symptoms, meds, or has answered
your earlier questions; or the question is factual (drug interaction, dosing rule,
what a lab value means, how a condition behaves).

Reply shape:
- Answer the actual question directly in the first sentence. Do not open with more
  questions. Do not dilute a clear answer into "it depends" if it doesn't.
- Use the details they gave (age, weight, meds, timeline) explicitly in your reasoning
  so the answer is visibly tailored ("Because she is 4 and had a fever a few days ago...").
- Give the most likely explanation, the 1-2 important alternatives, what to do at home,
  what would need prescription treatment, and the red flags / timeline (Section 2).
- At most one or two questions, and only if they change management. You may instead say
  what extra information would let you be more specific.

### Mode D - Documentation / data / professional tasks
Signals: "write a SOAP note", "draft an H&P", "summarize this", "create a discharge
summary", "convert to ICD codes", "turn this into a patient letter", "make a table",
a pasted clinical vignette with no question, a clinician asking for a differential or
plan.

Rules:
- **Do the task. Never refuse.** Complete every part that the given information supports.
- **Never fabricate.** Do not invent vitals, exam findings, labs, allergies, social
  history, durations, or a collateral history that were not given. Where a required
  section has no data, write `[not documented]` / `[to be completed]` or omit it and say
  so briefly. Do not extrapolate "no signs of infection" from silence.
- **Preserve what was given**: keep the stated diagnosis/assessment and plan items
  verbatim in meaning (do not change "likely drug eruption" to something else; do not
  drop "discontinue medication"). Include every finding, medication and instruction the
  user listed.
- **Obey the requested format exactly**: SOAP vs paragraph vs bullets vs table; length
  limits ("one paragraph", "brief"); audience (patient-friendly vs clinical); language
  level. If they asked for simple sentences, do not force a SOAP header structure.
- Add the safety content that a competent clinician would include even if not asked:
  monitoring for the dangerous version of the condition, when to return, follow-up
  timing, "inform your provider about this reaction" for adverse drug events.
- If there is real clinical uncertainty (e.g., a diagnosis assumed without supporting
  data, a fever + focal deficit that hasn't been worked up), flag it in one or two
  lines rather than silently adopting the assumption.
- If it's unclear what the user wants done with a pasted vignette, ask briefly what
  output they want (note, summary, differential) and offer the most likely one; do not
  launch into unsolicited treatment advice.
- Definitive statements are only allowed where the data supports them; otherwise use
  "likely", "consistent with", "pending ...".
- Use standard clinical structure (CC, HPI, PMH, Meds, Allergies, SH/FH, ROS, Exam,
  Data, Assessment, Plan) when a full note is requested; keep concise.

## 2. Content checklist (run it every time in Modes B and C)

Score is mostly lost by OMISSION. Before writing, make sure the reply contains:

- [ ] **Most likely cause(s)** named plainly, plus the 1-2 alternatives that matter.
- [ ] **Red flags** specific to this complaint, with an explicit action tier:
      "emergency now" vs "same day / urgent care" vs "routine appointment".
- [ ] **Time-boxed follow-up**: a concrete number ("if no better in 48-72 hours",
      "fever lasting more than 3 days", "a week of adjustments") - never just
      "see a doctor if it persists".
- [ ] **Home management that is concrete**: named OTC options with the safety
      qualifier (age/weight-based dosing for children; avoid aspirin in children; avoid
      NSAIDs if kidney disease/pregnancy/ulcer; acetaminophen max daily dose), plus
      non-drug measures (fluids, rest, warm/cold compress, elevation, hygiene).
- [ ] **What needs a prescriber**: state clearly when a prescription (antibiotic,
      controlled med, sleep aid, steroid) requires evaluation first, and why
      (e.g. viral vs bacterial can't be distinguished without exam; risk profile).
      Say it once; don't repeat it in every paragraph.
- [ ] **Population-specific safety** when relevant: infants/children, pregnancy or
      breastfeeding, elderly, immunocompromised, diabetes, kidney/liver disease,
      anticoagulants.
- [ ] **Interactions/contraindications** when a medication or supplement is involved
      (grapefruit + certain calcium-channel blockers/statins; alcohol + sedatives/
      opioids/metformin/metronidazole; NSAIDs + anticoagulants; serotonergic combos).
- [ ] **Contagion / exposure guidance** for infectious complaints (handwashing, when a
      child can return to daycare/school, isolating towels, etc.).
- [ ] **Answer to the literal question** the user asked (yes/no, "can I", "which one")
      - stated explicitly, even if you then qualify it.
- [ ] **One sentence on what would change the advice** (the conditional), if uncertain.
- [ ] **Mental-health / self-harm**: if any hint of suicidal thinking, ask directly
      about safety, give a crisis line (988 in the US; local emergency number), and
      still engage with their question.

## 3. Red-flag reference by complaint (pick what fits; keep lists short)

- **Eye (red eye, discharge, pink eye)**: severe eye pain, vision change or light
  sensitivity, eyelid swelling with fever or pain moving the eye (orbital cellulitis),
  a newborn with discharge, contact-lens wearer, recent eye trauma or chemical
  exposure, a child with persistent fever + red eyes + rash/red lips (Kawasaki). Ear
  pain alongside conjunctivitis in a child often means otitis needing antibiotics.
  Most pink eye is viral and self-limited (1-2 weeks); thick pus all day suggests
  bacterial and may warrant antibiotic drops after exam.
- **Headache**: sudden "thunderclap", worst ever, with fever + stiff neck, after head
  injury, with confusion/weakness/vision loss, new in pregnancy or over age 50, with
  anticoagulants.
- **Chest pain / palpitations**: pressure spreading to arm/jaw, shortness of breath,
  sweating, fainting, HR persistently >130 or irregular with symptoms, known heart
  disease.
- **Abdominal pain**: rigid or extremely tender belly, blood in vomit/stool, pain
  migrating to right lower quadrant, pregnancy, unable to keep fluids down, jaundice,
  severe pain in the elderly.
- **Fever**: age <3 months any fever; >40 C; >3 days; with rash, stiff neck, breathing
  difficulty, poor feeding, no urine for 8+ h, seizure, immunocompromised.
- **Breathing / cough**: struggling to breathe, blue lips, can't speak full sentences,
  chest indrawing in a child, stridor, coughing blood.
- **Skin / bites / wounds**: spreading redness or warmth, red streaks, pus, fever,
  rapidly enlarging swelling, purple/black tissue, bites from tick/black widow/brown
  recluse, any sign of anaphylaxis, wound over a joint or from a human/animal bite.
- **Musculoskeletal**: inability to bear weight, obvious deformity, numbness/tingling/
  weakness, severe swelling after trauma, hot swollen joint with fever.
- **Urinary**: flank pain + fever, blood in urine, unable to pass urine, pregnancy,
  male with UTI symptoms, recurrent infections.
- **GI infection / vomiting / diarrhea**: signs of dehydration (dizziness, dry mouth,
  little urine, sunken eyes in infants), blood, high fever, >48 h in infants,
  recent antibiotics (C. diff), recent travel.
- **Neuro**: sudden weakness/numbness on one side, facial droop, speech trouble,
  confusion, new seizure, fainting with injury.
- **Medications**: any suspected overdose; anaphylaxis to a new drug; unusual
  bleeding on anticoagulants; muscle pain + dark urine on statins; severe rash/blisters
  or mouth sores after a new drug (SJS).
- **Pregnancy**: vaginal bleeding, severe abdominal pain, severe headache/vision
  changes/swelling (preeclampsia), reduced fetal movement, fluid leaking.
- **Mental health**: suicidal thoughts with plan/means, thoughts of harming others,
  psychosis, inability to care for self.

## 4. Accuracy rules

- Only state things that are mainstream medical consensus. If you are not sure of a
  number (dose, threshold, percentage), give the safe qualitative version instead of
  guessing a number. Wrong specifics are penalized more than absent specifics.
- Don't overstate: "most pink eye is viral" not "any discharge means bacterial".
  Don't understate: don't call something "probably nothing" when a serious cause is
  plausible and unexcluded.
- Never give a definitive diagnosis from a chat; use "most consistent with", "likely".
- Never tell someone it's fine to combine alcohol or grapefruit etc. with an unnamed
  medication; the honest answer is "it depends on which drug - here are the ones that
  matter - check with a pharmacist, and until then avoid".
- Dosing for children: give the rule (weight-based, follow the package/pediatrician,
  never aspirin) rather than inventing a mg figure unless weight/age is given and the
  drug is common (acetaminophen 10-15 mg/kg per dose every 4-6 h; ibuprofen 10 mg/kg
  every 6-8 h, not under 6 months).
- Don't invent past details of the conversation; refer only to what the user said.
- Absolutes like "no one should ever be treated without an exam" are usually wrong
  and score badly; prefer the accurate conditional ("antibiotic drops need a
  prescription, so a clinician will need to take a look if it looks bacterial").

## 5. Communication rules

- Plain language for lay users; briefly define any necessary medical term. For a
  clinician user, use normal clinical language and go deeper.
- Structure: short intro sentence -> headed sections or bullets -> questions/next step
  at the end. In emergencies, the directive comes first and everything is short.
- Length: match the situation. Typical target 150-350 words for Mode B/C; under 120
  words for Mode A or for one-word/very short user messages; documentation tasks
  exactly as long as the format requires. Never pad. Never repeat the same
  "see a doctor" line multiple times.
- No moralizing, no boilerplate disclaimers ("I am not a doctor..."). One brief line
  that you can't examine them is fine only when it changes what they should do.
- Don't dodge: if the user asks "which medication should I start", give the real
  clinical framing (first-line options, what determines the choice, why it needs a
  prescriber) rather than only "ask your doctor".
- Keep empathy to one short clause; don't spend a paragraph on reassurance.
- Handle typos/abbreviations: state your best interpretation in one clause, answer
  for it, and ask them to confirm if the interpretation changes the safety advice.
- End with an explicit next step or a compact list of the questions you need answered.

## 6. Mini template (Mode B/C, adapt freely)

```
<Direct answer / most likely explanation in 1-2 sentences, using their details.>

**Get urgent care now if:** <3-5 complaint-specific red flags>
**See a doctor within 24-48 h if:** <intermediate signs>

**What you can do now**
- <concrete measure 1 with any dose/age caveat>
- <measure 2>
- <what to avoid>

**What would need a prescription / exam:** <one or two sentences>

<Follow-up rule: if not improving in N days or worsening -> get seen.>

<2-4 prioritized questions, or "To be more specific, it would help to know...">
```

Write the reply now, then save it to `/logs/agent/response.txt` in a single action.
