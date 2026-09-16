# Damage Class Taxonomy

The definitive damage classes for the Qaddir project (TASK-03).

This ordering is **fixed**. It is written into `cardd.yaml` and baked into every
trained model, so changing it after training silently invalidates existing
weights. Any future change requires retraining and a new entry in this file.

Source dataset: CarDD (Wang, Li & Wu, *IEEE T-ITS* 24(7):7202–7214, 2023).

## Final classes

| YOLO class ID | Class name | CarDD category ID | Original CarDD name |
|---|---|---|---|
| 0 | `dent` | 1 | dent |
| 1 | `scratch` | 2 | scratch |
| 2 | `crack` | 3 | crack |
| 3 | `glass_shatter` | 4 | glass shatter |
| 4 | `lamp_broken` | 5 | lamp broken |
| 5 | `tire_flat` | 6 | tire flat |

Class IDs are assigned by ascending CarDD category ID. CarDD's IDs are already
contiguous (1–6), so the mapping is a straight shift to zero-based indexing.

## Definitions and boundary rules

Each class carries a boundary rule for the case it is most often confused with,
so annotators and reviewers resolve disagreements the same way.

**0 · `dent`** — Deformation of a panel where the metal or plastic is pushed out
of shape, with the surface finish largely intact.
*Boundary:* if the paint is broken but the panel keeps its shape, it is
`scratch`, not `dent`. A dent that is also scratched is annotated as both.

**1 · `scratch`** — Damage to the surface finish only: paint scraped, scuffed or
worn away, with the underlying panel undeformed.
*Boundary:* surface-level only. If the material is split through its thickness
it is `crack`. If the panel shape is altered it is also `dent`.

**2 · `crack`** — A split or fracture through the material itself, typically in
a bumper, trim or plastic light housing.
*Boundary:* through-material, unlike `scratch`, which is surface-only. Cracked
window glass is `glass_shatter`; a cracked lamp lens is `lamp_broken`.

**3 · `glass_shatter`** — Fractured, spidered or missing window glass:
windscreen, side windows or rear screen.
*Boundary:* window glass only. Damage to a headlight or tail-light lens is
`lamp_broken`, regardless of how similar the fracture pattern looks.

**4 · `lamp_broken`** — Damage to a light unit: headlight, tail-light or
indicator, whether cracked, shattered, or with the lens missing.
*Boundary:* the lamp assembly, including its lens. Window glass is
`glass_shatter`.

**5 · `tire_flat`** — A visibly deflated or destroyed tyre.
*Boundary:* the tyre only, not the wheel rim. This is the only class that is not
bodywork damage.

## Decisions

**All six CarDD classes are kept. No class was merged or excluded.**

Each class corresponds to a different repair action, which is the purpose of a
damage assessment. Merging any pair would remove information the generated
report needs.

**`crack` was considered for merging into `scratch` and deliberately kept
separate.** Both look linear and `crack` is the hardest class to detect (median
instance area 1,534 px, roughly a twentieth of `dent`). They were kept apart
because a scratch is surface paint while a crack is through-material: different
severity, different repair, different cost.

**`tire_flat` was considered for exclusion and kept.** At 3.6% of instances it
is the rarest class, but it is safety-relevant and visually unambiguous, and a
damage report that silently ignores flat tyres would be misleading.

**Three classes were renamed to snake_case:** `glass shatter` → `glass_shatter`,
`lamp broken` → `lamp_broken`, `tire flat` → `tire_flat`. Spaces in class names
cause problems in YAML, file names and command-line arguments. The change is
cosmetic; no class was merged or redefined.

## Distribution

Measured across all three CarDD splits (8,740 instances in 4,000 images).

| Class | Train | Val | Test | Total | Share | Median area (px) |
|---|---|---|---|---|---|---|
| `dent` | 1806 | 501 | 236 | 2543 | 29.1% | 35,401 |
| `scratch` | 2560 | 728 | 307 | 3595 | 41.1% | 19,574 |
| `crack` | 651 | 177 | 70 | 898 | 10.3% | 1,534 |
| `glass_shatter` | 475 | 135 | 71 | 681 | 7.8% | 352,228 |
| `lamp_broken` | 494 | 141 | 69 | 704 | 8.1% | 87,738 |
| `tire_flat` | 225 | 62 | 32 | 319 | 3.6% | 180,041 |
| **Total** | **6211** | **1744** | **785** | **8740** | | |

Median areas are rounded to the nearest pixel; `crack` and `lamp_broken` have
even instance counts, so their exact medians are 1533.5 and 87737.5.

Two consequences for later tasks:

- **Class imbalance is 11.3×** between `scratch` and `tire_flat`. Not severe
  enough to exclude a class, but per-class metrics must be reported rather than
  a single averaged figure, and imbalance is a candidate lever for the
  improvement experiment.
- **Median instance areas span 230×**, from `crack` at 1,534 px to
  `glass_shatter` at 352,228 px. `crack` is expected to be the weakest class and
  is the one to watch during baseline evaluation.

## For conversion, training and evaluation code

Class list for the Ultralytics dataset YAML, in the fixed order above:

```yaml
names:
  0: dent
  1: scratch
  2: crack
  3: glass_shatter
  4: lamp_broken
  5: tire_flat
```

The conversion notebook assigns class IDs by sorting CarDD category IDs
ascending, which reproduces this table exactly. Conversion must apply the
snake_case names when writing the YAML; the CarDD JSON itself is never modified.

All CarDD annotations were verified to be single simple polygons: **zero RLE,
zero `iscrowd`, and zero multi-polygon annotations** across all three splits. No
annotation is dropped or split by the conversion for these reasons.
