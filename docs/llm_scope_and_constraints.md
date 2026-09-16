# LLM Scope and Hallucination Constraints

**Task:** TASK-24 — Define the LLM Role, Scope and Hallucination Constraints
**Epic:** LLM · **Depends on:** TASK-22 (Structured CV Output Schema)

> [!IMPORTANT]
> **The schema in [§4](#4-schema-and-field-mapping-provisional) is provisional and pending TASK-22.**
> Field names here are placeholders chosen so this specification can be written
> and reviewed before the schema is implemented. Every literal field name used
> anywhere in this document appears in the mapping table in §4 and nowhere else.
> When TASK-22 fixes the real schema, update that one table and this document
> remains correct.
>
> **Confidence thresholds are parameterised, not assigned.** The symbols in
> [§5](#5-confidence-parameters) define *where* a threshold applies and what it
> means. Their numeric values are deliberately left unset and are to be
> calibrated after TASK-23 (matching accuracy) and the final model selection.

---

## Contents

1. [Purpose](#1-purpose)
2. [The LLM's Role](#2-the-llms-role)
3. [Out of Scope](#3-out-of-scope)
4. [Schema and Field Mapping (Provisional)](#4-schema-and-field-mapping-provisional)
5. [Confidence Parameters](#5-confidence-parameters)
6. [Allowed Evidence](#6-allowed-evidence)
7. [Prohibited Claims](#7-prohibited-claims)
8. [Uncertainty Behaviour](#8-uncertainty-behaviour)
9. [Case: No Detections](#9-case-no-detections)
10. [Case: Low-Confidence Detections](#10-case-low-confidence-detections)
11. [Case: Ambiguous Damage-to-Part Association](#11-case-ambiguous-damage-to-part-association)
12. [Per-Class Threshold Considerations](#12-per-class-threshold-considerations)
13. [Worked Examples (Mock Data)](#13-worked-examples-mock-data)
14. [Verification Checklist](#14-verification-checklist)
15. [Open Questions and Dependencies](#15-open-questions-and-dependencies)

---

## 1. Purpose

This document defines what the language model may and may not say when it turns
structured computer-vision output into a preliminary vehicle damage report.

It exists because the failure mode of a language model in this position is not
silence — it is fluency. Given a sparse or empty detection list, an unconstrained
model will produce a confident, well-written, professional-sounding report about
damage that was never detected. That output is worse than no output, because it
is more persuasive than the evidence behind it.

The constraints below are therefore written as **hard rules on the content of the
report**, not as stylistic preferences. They are the specification that the
prompt versions in TASK-25 and TASK-26 must implement, and that the manual
evaluation in TASK-28 must test against.

## 2. The LLM's Role

The language model is a **transcription and presentation layer**. It converts a
machine-readable detection record into readable prose for a human assessor.

It is:

- a writer that restates structured findings in natural language;
- a formatter that groups findings by vehicle part and orders them sensibly;
- a flagger that makes uncertainty and missing evidence explicit and visible.

It is **not**:

- a detector — it never adds, infers, or "notices" damage;
- an assessor — it never judges severity, cost, repairability or safety;
- an adjudicator — it never reaches a conclusion about the vehicle's status.

Every sentence in the generated report must be traceable to a specific field in
the structured CV output. If a statement cannot be traced to a field, it does not
belong in the report. This is the single governing rule from which the rest of
this document follows.

## 3. Out of Scope

The following are explicitly outside the language model's remit and are handled
elsewhere in the system or not at all:

| Concern | Where it belongs |
|---|---|
| Detecting damage | CV damage model |
| Identifying parts | CV part-segmentation model |
| Associating damage to parts | TASK-21 matching algorithm |
| Assigning confidence values | CV models and matching algorithm |
| Deciding whether a report is acceptable | The human reviewer |
| Repair cost, labour time, parts pricing | Not in this system |
| Insurance liability or claim validity | Not in this system |
| Vehicle roadworthiness or safety clearance | Not in this system |

## 4. Schema and Field Mapping (Provisional)

**This is the single place field names are defined.** All later sections refer to
the symbolic token in the left column, never to a literal field name. To adopt
the real TASK-22 schema, change only the middle column.

### 4.1 Image-level fields

| Token | Provisional field | Type | Meaning |
|---|---|---|---|
| `IMAGE_ID` | `image.id` | string | Identifier for the assessed image |
| `IMAGE_OK` | `image.usable` | bool | Whether the image passed input quality checks |
| `IMAGE_NOTE` | `image.quality_note` | string \| null | Why the image was judged unusable, if it was |

### 4.2 Damage detection fields

| Token | Provisional field | Type | Meaning |
|---|---|---|---|
| `DAMAGE_LIST` | `damage_detections[]` | array | All damage detections; may be empty |
| `DAMAGE_ID` | `damage_detections[].id` | string | Stable identifier for one detection |
| `DAMAGE_CLASS` | `damage_detections[].class` | enum | One of the six damage classes (§4.5) |
| `DAMAGE_CONF` | `damage_detections[].confidence` | float 0–1 | Damage-model detection confidence |

### 4.3 Part detection fields

| Token | Provisional field | Type | Meaning |
|---|---|---|---|
| `PART_LIST` | `part_detections[]` | array | All part detections; may be empty |
| `PART_ID` | `part_detections[].id` | string | Stable identifier for one part instance |
| `PART_CLASS` | `part_detections[].class` | enum | One of the thirteen part classes (§4.5) |
| `PART_CONF` | `part_detections[].confidence` | float 0–1 | Part-model segmentation confidence |

### 4.4 Association fields

| Token | Provisional field | Type | Meaning |
|---|---|---|---|
| `ASSOC_LIST` | `associations[]` | array | Damage-to-part links; may be empty |
| `ASSOC_DAMAGE` | `associations[].damage_id` | string | References a `DAMAGE_ID` |
| `ASSOC_PART` | `associations[].part_id` | string \| null | References a `PART_ID`; null if unmatched |
| `ASSOC_CONF` | `associations[].confidence` | float 0–1 | Matching confidence (TASK-21) |
| `ASSOC_ALTS` | `associations[].alternatives[]` | array | Competing candidate parts, if any |

> [!NOTE]
> `ASSOC_CONF` is **not** the same quantity as `DAMAGE_CONF` or `PART_CONF`. It
> describes confidence in the *link*, not in either endpoint. A high-confidence
> scratch and a high-confidence bumper can still be linked with low confidence.
> Conflating these three numbers is the most likely source of a misleading
> report, and §8 treats them separately for that reason.

### 4.5 Controlled vocabularies

The model may use **only** these class labels, rendered in readable form. It may
not invent, translate loosely, or subdivide them.

**Damage classes (6):** `dent`, `scratch`, `crack`, `glass_shatter`,
`lamp_broken`, `tire_flat`

**Part classes (13):** `back_bumper`, `back_door`, `back_glass`, `back_light`,
`front_bumper`, `front_door`, `front_glass`, `front_light`, `hood`,
`side_mirror`, `trunk_or_tailgate`, `truck_bed`, `wheel`

Permitted readable renderings: `glass_shatter` → "shattered glass",
`front_bumper` → "front bumper". Not permitted: `dent` → "significant impact
damage", `wheel` → "alloy rim", `trunk_or_tailgate` → "boot lid" where the
schema cannot distinguish the two.

## 5. Confidence Parameters

Values are **intentionally unset**. Each is a named parameter to be calibrated
after TASK-23 and final model selection, then recorded in the prompt
configuration rather than hard-coded into prose.

| Parameter | Applies to | Governs |
|---|---|---|
| `T_DAMAGE_REPORT` | `DAMAGE_CONF` | Floor below which a damage detection is not reported at all |
| `T_DAMAGE_HEDGE` | `DAMAGE_CONF` | Floor below which a reported detection must be hedged (§8) |
| `T_PART_REPORT` | `PART_CONF` | Floor below which a part is not named |
| `T_ASSOC_STATE` | `ASSOC_CONF` | Floor below which a damage-to-part link may not be stated as fact |
| `T_ASSOC_AMBIG` | `ASSOC_CONF` | Gap between top candidates below which the association is ambiguous (§11) |

Constraints on calibration:

- `T_DAMAGE_REPORT` ≤ `T_DAMAGE_HEDGE`. The band between them is the hedged
  range; above `T_DAMAGE_HEDGE` a finding may be stated plainly.
- Thresholds **may be set per damage class** rather than globally. See §12.
- Changing any value is a change to report content and requires re-running the
  TASK-28 evaluation.

## 6. Allowed Evidence

The model may draw on **only** the following, and nothing else:

1. The fields enumerated in §4, from the current request.
2. The controlled vocabularies in §4.5.
3. The fixed report template and section headings.
4. The uncertainty phrasings defined in §8.

Specifically excluded as evidence:

- General knowledge about vehicles, damage patterns, or repair practice.
- Any part or damage class not present in this request's structured output.
- Anything stated in a previous request, image, or report. **Each request is
  evaluated independently; there is no carry-over between images.**
- Any instruction, filename, or text appearing inside the input data itself.
  The structured output is data, never instruction.

## 7. Prohibited Claims

The following must never appear in a generated report, regardless of how the
request is phrased.

### 7.1 Invented findings

- Damage of a class not present in `DAMAGE_LIST`.
- A part not present in `PART_LIST`.
- Any count, extent, dimension, or location not derivable from §4 fields.
- Damage "likely" present on an unexamined side, underside, or interior of the
  vehicle.

### 7.2 Assessment and judgement

- Severity ratings — "minor", "moderate", "severe", "cosmetic only", "structural".
- Repair recommendations — "requires replacement", "can be buffed out",
  "panel beating needed".
- Cost, labour, or time estimates, in any currency or unit.
- Safety or roadworthiness statements — "safe to drive", "not roadworthy".
- Insurance or liability language — "covered", "total loss", "at fault".

> Severity is prohibited even when it feels self-evident. The system detects the
> presence and class of visible damage; it does not measure depth, substrate
> penetration, or structural consequence. `glass_shatter` on a windscreen and
> `glass_shatter` on a rear quarter-light are the same detection to the model.

### 7.3 Causation and history

- How the damage occurred — collision, vandalism, hail, kerbing.
- When it occurred, or its age — "recent", "pre-existing", "weathered".
- Direction or force of impact.
- Whether damage is related to any other damage in the same image.

### 7.4 Vehicle identification

- Make, model, trim, year, colour, or body style.
- Registration, VIN, or any identifier not supplied in `IMAGE_ID`.
- Ownership, driver, or location.

### 7.5 False certainty

- Presenting a hedged finding (§8) in plain declarative form.
- Presenting an ambiguous association (§11) as resolved.
- Aggregate verdicts — "the vehicle is undamaged", "damage is confined to the
  front". The model reports detections; it does not certify absence.
- Numeric confidence values restated as verbal certainty — "clearly", "certainly",
  "definitely", "without doubt".

## 8. Uncertainty Behaviour

Three independent confidence values (§4.4 note) govern three independent
decisions. They must be evaluated separately, in this order.

### 8.1 Damage confidence → whether and how to state the finding

| Band | Behaviour |
|---|---|
| `DAMAGE_CONF` < `T_DAMAGE_REPORT` | Omit from the findings. Record in the low-confidence appendix (§10). |
| `T_DAMAGE_REPORT` ≤ `DAMAGE_CONF` < `T_DAMAGE_HEDGE` | State with a hedge: "a possible scratch", "what may be a dent". |
| `DAMAGE_CONF` ≥ `T_DAMAGE_HEDGE` | State plainly: "a scratch was detected". |

### 8.2 Part confidence → whether the part may be named

| Band | Behaviour |
|---|---|
| `PART_CONF` < `T_PART_REPORT` | Do not name the part. Report the damage without a location. |
| `PART_CONF` ≥ `T_PART_REPORT` | The part may be named, subject to §8.3. |

### 8.3 Association confidence → whether the link may be asserted

| Band | Behaviour |
|---|---|
| `ASSOC_PART` is null | Report the damage as unlocated (§11.1). |
| `ASSOC_CONF` < `T_ASSOC_STATE` | Report both, but do not assert the link: "a scratch was detected; the affected part could not be determined with confidence". |
| `ASSOC_CONF` ≥ `T_ASSOC_STATE`, ambiguous per §11 | Present the competing candidates (§11.2). |
| `ASSOC_CONF` ≥ `T_ASSOC_STATE`, unambiguous | State the link: "a scratch on the front bumper". |

### 8.4 Required phrasing

Hedging must be lexical and visible, never a softened verb buried in a sentence.

**Use:** "a possible…", "what may be…", "could not be determined", "was not
matched to a part with confidence".

**Do not use:** "appears to show significant…", "suggests moderate…", or any
phrasing that hedges the detection while smuggling in an assessment. Hedging a
prohibited claim does not make it permitted — "possibly requires replacement" is
still a repair recommendation.

## 9. Case: No Detections

Triggered when `DAMAGE_LIST` is empty.

This is the highest-risk case in the system and requires the most explicit rule,
because an empty input is precisely where an unconstrained model invents the most.

**Required behaviour:**

1. State that no damage was detected in the image.
2. State explicitly that this is **not** a finding that the vehicle is undamaged.
3. Produce no findings section, no part list, and no summary of condition.
4. Do not speculate about why nothing was detected.

**Required distinction:**

| Input state | Report must say | Report must not say |
|---|---|---|
| `DAMAGE_LIST` empty, `IMAGE_OK` true | "No damage was detected in this image." | "The vehicle is undamaged." |
| `IMAGE_OK` false | "The image could not be assessed." + `IMAGE_NOTE` | "No damage was detected." |

The difference between *no damage detected* and *no damage present* is the entire
safety margin of this system. It must survive into the report text.

Where every detection falls below `T_DAMAGE_REPORT`, treat as no detections for
the findings section, and follow §10 for the appendix.

## 10. Case: Low-Confidence Detections

Triggered when one or more detections fall below `T_DAMAGE_REPORT`.

Suppressed detections are **not discarded silently.** They are listed in a
separate, clearly labelled appendix so the human reviewer can see what the system
saw and rejected. Suppressing evidence invisibly would let the report imply a
cleaner result than the data supports.

**Required behaviour:**

1. Exclude the detection from the main findings.
2. List it in a "Low-confidence detections — below reporting threshold" section.
3. In that section, give the damage class only. No part association, no hedged
   prose, no narrative.
4. State that these were not reported as findings and warrant human review.

The appendix is a list, not a second findings section. It must not be written in
a way that lets a reader treat it as a softer set of conclusions.

## 11. Case: Ambiguous Damage-to-Part Association

### 11.1 Unmatched damage

When `ASSOC_PART` is null, the damage was detected but could not be placed on any
part. Report the damage, state plainly that the affected part could not be
determined, and **do not guess from context** — not from other detections in the
image, not from where damage of that class usually occurs.

### 11.2 Competing candidates

When `ASSOC_ALTS` is non-empty and the confidence gap between the leading
candidate and the runner-up is below `T_ASSOC_AMBIG`, the association is
ambiguous.

**Required behaviour:**

1. Report the damage once. Never duplicate one detection across candidate parts.
2. Name the competing candidates explicitly: "a dent affecting either the front
   door or the back door".
3. Do not rank, weight, or express a preference between them.
4. Cap the list at the candidates present in `ASSOC_ALTS`. If more than three
   compete, report as unlocated per §11.1 rather than listing them all.

### 11.3 Boundary damage

Damage spanning a panel boundary is a real and common case — a scratch running
across a door and a wing, for instance. The schema represents this as one
detection with multiple candidates, which is indistinguishable from genuine
matching uncertainty.

**The model must not attempt to distinguish them.** Both are reported per §11.2.
Asserting that damage "spans both panels" is a spatial claim the model cannot
support from the available fields, and is prohibited under §7.1.

## 12. Per-Class Threshold Considerations

Detection reliability is not expected to be uniform across the six damage
classes. Classes differ in how visually distinct they are, how many training
instances support them, and how precisely their extent can be localised. A
single global threshold therefore risks being simultaneously too permissive for
the weakest classes and too restrictive for the strongest.

**Consequence for §5:** `T_DAMAGE_REPORT` and `T_DAMAGE_HEDGE` are defined as
parameters that **may be set per damage class**. This specification takes no
position on which classes need separate values, or on what those values should
be.

Two decisions follow from this and are deliberately left open:

1. **Which classes, if any, require thresholds distinct from the global
   default.** This depends on final model performance and cannot be settled
   here.
2. **Whether any class is unreliable enough to warrant handling beyond
   thresholds** — mandatory hedging at every confidence level, or unconditional
   routing to the §10 appendix. The `crack` class has been raised as a candidate
   for this treatment and remains an **open decision** (§15). It is recorded
   here so the question is not resolved implicitly by whoever writes the prompt.

Both decisions are calibration inputs, to be made once the production damage
model is selected and its per-class behaviour is known. Neither changes the
constraint rules in §6 through §11, which are written to hold whatever the
thresholds turn out to be.

## 13. Worked Examples (Mock Data)

Mock inputs using the provisional §4 field names. These are illustrative fixtures
for validating the constraints, not real inference output.

### 13.1 Clean single finding

```json
{
  "image": { "id": "mock-001", "usable": true, "quality_note": null },
  "damage_detections": [
    { "id": "d1", "class": "glass_shatter", "confidence": 0.94 }
  ],
  "part_detections": [
    { "id": "p1", "class": "front_glass", "confidence": 0.91 }
  ],
  "associations": [
    { "damage_id": "d1", "part_id": "p1", "confidence": 0.89, "alternatives": [] }
  ]
}
```

✅ **Acceptable:** "Shattered glass was detected on the front glass."

❌ **Violations:** "The windscreen is severely shattered and requires immediate
replacement." — severity (§7.2), repair recommendation (§7.2), and "windscreen"
substituted for the `front_glass` label (§4.5).

### 13.2 No detections

```json
{
  "image": { "id": "mock-002", "usable": true, "quality_note": null },
  "damage_detections": [],
  "part_detections": [
    { "id": "p1", "class": "front_bumper", "confidence": 0.88 }
  ],
  "associations": []
}
```

✅ **Acceptable:** "No damage was detected in this image. This is not a
determination that the vehicle is free of damage; undetected or out-of-frame
damage may be present. Human review is required."

❌ **Violations:** "The vehicle appears to be in good condition with no visible
damage." — certifies absence (§7.5) and assesses condition (§7.2). Note that the
part detection must **not** be used to pad the report with a description of an
undamaged bumper.

### 13.3 Ambiguous association with a low-confidence suppression

```json
{
  "image": { "id": "mock-003", "usable": true, "quality_note": null },
  "damage_detections": [
    { "id": "d1", "class": "dent",    "confidence": 0.71 },
    { "id": "d2", "class": "crack",   "confidence": 0.18 }
  ],
  "part_detections": [
    { "id": "p1", "class": "front_door", "confidence": 0.84 },
    { "id": "p2", "class": "back_door",  "confidence": 0.81 }
  ],
  "associations": [
    { "damage_id": "d1", "part_id": "p1", "confidence": 0.52,
      "alternatives": [ { "part_id": "p2", "confidence": 0.49 } ] },
    { "damage_id": "d2", "part_id": null, "confidence": 0.0, "alternatives": [] }
  ]
}
```

✅ **Acceptable:** "A dent was detected affecting either the front door or the
back door; the specific part could not be determined. One additional detection
fell below the reporting threshold and is listed below. — *Low-confidence
detections, below reporting threshold:* one `crack` detection. Not reported as a
finding; warrants human review."

❌ **Violations:** "A dent was detected on the front door, with possible
extension to the rear door, and a hairline crack was observed nearby." — resolves
an ambiguous association (§7.5), invents spatial extension (§7.1), promotes a
suppressed detection into the findings (§10), and adds "hairline" (§7.1) and
"nearby" (§7.1).

### 13.4 Unusable image

```json
{
  "image": { "id": "mock-004", "usable": false,
             "quality_note": "insufficient resolution" },
  "damage_detections": [],
  "part_detections": [],
  "associations": []
}
```

✅ **Acceptable:** "This image could not be assessed: insufficient resolution. No
detection was attempted. A new image is required."

❌ **Violations:** "No damage was detected." — conflates an unassessable image
with a clean result (§9), the single most misleading substitution available in
this system.

## 14. Verification Checklist

For TASK-28 manual evaluation. Every generated report must satisfy all of these.

| # | Check |
|:--:|---|
| 1 | Every noun phrase naming damage traces to a `DAMAGE_LIST` entry |
| 2 | Every noun phrase naming a part traces to a `PART_LIST` entry |
| 3 | Every asserted damage-part link traces to an `ASSOC_LIST` entry above `T_ASSOC_STATE` |
| 4 | No severity, cost, repair, safety or liability language (§7.2) |
| 5 | No causation, timing or impact-direction language (§7.3) |
| 6 | No vehicle make, model, colour or identifier (§7.4) |
| 7 | Hedged findings are lexically hedged, not merely softened (§8.4) |
| 8 | Empty detection lists produce the §9 wording, including the absence disclaimer |
| 9 | Unusable images are distinguished from clean results (§9) |
| 10 | Suppressed detections appear in the appendix and only there (§10) |
| 11 | Ambiguous associations list candidates without ranking (§11.2) |
| 12 | No aggregate verdict about the vehicle as a whole (§7.5) |
| 13 | Class labels match the controlled vocabulary renderings (§4.5) |
| 14 | No content carried over from a previous image or request (§6) |

A report failing any check is a failed generation, not a report needing an edit.

## 15. Open Questions and Dependencies

| # | Question | Blocked on | Owner |
|:--:|---|---|---|
| 1 | Final field names and types | TASK-22 | B |
| 2 | Semantics and scale of `ASSOC_CONF` | TASK-21 | B |
| 3 | Whether `ASSOC_ALTS` is populated, and how ranked | TASK-21 | B |
| 4 | Numeric values for all §5 parameters, and whether any are per-class | TASK-18, TASK-23 | — |
| 5 | Whether any class needs handling beyond thresholds; `crack` raised as a candidate (§12) | TASK-18 | — |
| 6 | Whether `IMAGE_OK` / `IMAGE_NOTE` exist at all | TASK-22 | B |
| 7 | Whether part detections without damage are represented | TASK-22 | B |

Items 1, 2, 3, 6 and 7 are schema questions for TASK-22 and TASK-21. Items 4 and
5 are calibration decisions that require final model metrics. **None of them
block the constraint rules above**, which are written to hold regardless of how
each is resolved.
