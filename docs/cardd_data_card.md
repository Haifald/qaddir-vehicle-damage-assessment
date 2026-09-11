# CarDD Dataset Data Card

## 1. Dataset Overview

CarDD is used in the Qaddir project for vehicle damage detection from images.
The dataset is used to identify and localize visible vehicle damage for a preliminary,
AI-assisted assessment workflow.

## 2. Dataset Structure

The dataset is provided in COCO format and contains three predefined splits:

| Split | Images | Annotations |
|---|---:|---:|
| Train | 2,816 | 6,211 |
| Validation | 810 | 1,744 |
| Test | 374 | 785 |
| **Total** | **4,000** | **8,740** |

## 3. Damage Classes

The dataset contains six damage categories:

1. Dent
2. Scratch
3. Crack
4. Glass Shatter
5. Lamp Broken
6. Tire Flat

## 4. Annotation Format

The original dataset contains COCO-format JSON annotation files:

- `instances_train2017.json`
- `instances_val2017.json`
- `instances_test2017.json`

Each annotation includes a damage category and bounding-box information.

## 5. Dataset Statistics

The dataset contains 4,000 unique images, all of which have annotations.

Average image dimensions are approximately 978 × 706 pixels.
The median image dimensions are 1,000 × 667 pixels.

The average number of annotated damage instances per image is 2.185,
with a maximum of 13 instances in a single image.

## 6. Class Distribution

The number of damage annotations is:

| Damage Class | Annotations |
|---|---:|
| Scratch | 3,595 |
| Dent | 2,543 |
| Crack | 898 |
| Lamp Broken | 704 |
| Glass Shatter | 681 |
| Tire Flat | 319 |

The distribution is imbalanced, with Scratch being the most frequent class
and Tire Flat being the least frequent class.

## 7. Bounding-Box Characteristics

Damage regions vary considerably in size across classes. Crack annotations
have relatively small bounding boxes compared with the other damage categories,
while Glass Shatter annotations tend to occupy larger image regions.

## 8. Data Preparation

The original CarDD COCO annotations were converted to YOLO format for use
with the object detection training pipeline.

The converted dataset preserves the Train, Validation, and Test split structure.

## 9. Intended Use

The dataset is used within the Qaddir graduation project to develop and evaluate
an AI-assisted preliminary vehicle damage detection system.

The system is intended to support human review and is not intended to replace
professional vehicle assessment.

## 10. Limitations

The dataset has notable class imbalance, particularly between frequently represented
classes such as Scratch and less frequent classes such as Tire Flat.

Small damage regions, especially Crack annotations, may present additional
challenges for object detection.

The dataset should therefore not be interpreted as a complete representation
of all real-world vehicle damage conditions.

## 11. License and Usage Restrictions

License and usage restrictions for the original CarDD dataset have not been
documented in the current project sources and must be verified from the original
dataset source before external redistribution or commercial use.

## 12. Related Project Reference

The project also references the Professional Standards for Vehicle Damage Assessment
published by the Saudi Authority for Accredited Valuers (Taqeem).

## 13. Provenance

The dataset was obtained as `CarDD_release.zip` and analyzed from its COCO-format
release. The project repository does not include the original dataset files.

## 14. Disclaimer

Qaddir is a proof-of-concept project. AI-generated results are intended for
preliminary assistance and human review and do not replace professional vehicle
damage assessment.
