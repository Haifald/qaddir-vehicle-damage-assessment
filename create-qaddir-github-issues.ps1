$repo = "Haifald/qaddir-vehicle-damage-assessment"

Write-Host "Checking GitHub CLI authentication..."
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login"
    exit 1
}

Write-Host "Creating 40 GitHub Issues in $repo..."

Write-Host "Creating TASK-01..."
$title = "[TASK-01] Acquire, Stage and License-Check the CarDD Dataset"
$body = @'
## Task Description
Download the official CarDD dataset from its approved source. Keep an unchanged raw copy, organise it in the project data folders, and record the source, version/date, licence and any usage restrictions.

## Task Details
- **Epic:** Foundation
- **Owner:** A
- **Priority:** High
- **Depends on:** None

## Definition of Done
Raw CarDD files are accessible in the expected folder; source and licence are documented; the raw copy has not been modified.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-01. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-02..."
$title = "[TASK-02] Establish Repository Engineering Baseline (src/ package, dependencies, notebook policy)"
$body = @'
## Task Description
Set up the repository so every team member can run the project consistently. Create the src/ package structure, dependency/environment file, basic configuration layout, and clear rules for notebook names, outputs and reusable code.

## Task Details
- **Epic:** Foundation
- **Owner:** C
- **Priority:** High
- **Depends on:** None

## Definition of Done
A clean environment can install the dependencies; src/ imports work; the agreed repository and notebook conventions are documented.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-02. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-03..."
$title = "[TASK-03] Define the Final Damage Class Taxonomy"
$body = @'
## Task Description
Review the CarDD damage labels and decide the exact damage classes the project will use. Document any renamed, merged or excluded classes and create a fixed mapping from the original labels to the final taxonomy.

## Task Details
- **Epic:** Foundation
- **Owner:** A
- **Priority:** High
- **Depends on:** None

## Definition of Done
The final damage-class list and label mapping are documented, unambiguous and ready to be used by conversion, training and evaluation code.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-03. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-04..."
$title = "[TASK-04] Define the Final Vehicle-Part Class Taxonomy and Resolve Notebook 03 Findings"
$body = @'
## Task Description
Review the vehicle-part dataset and the issues identified in Notebook 03. Decide which part classes to keep, merge, rename or remove, and document how problematic annotations or classes will be handled.

## Task Details
- **Epic:** Foundation
- **Owner:** B
- **Priority:** High
- **Depends on:** None

## Definition of Done
The final part-class list and mapping are fixed; every relevant Notebook 03 issue has a documented decision and resolution.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-04. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-05..."
$title = "[TASK-05] Cross-Domain Feasibility Spike: Vehicle-Part Model on Damaged-Car Imagery"
$body = @'
## Task Description
Test the current or pretrained vehicle-part detector on a representative sample of damaged-car images. Inspect the predictions, measure the domain gap, identify common failures, and use the evidence to decide whether the planned part-detection approach is viable.

## Task Details
- **Epic:** Foundation
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-01

## Definition of Done
Prediction examples and a short feasibility result are saved; the domain gap is described; the vehicle-part modelling approach is explicitly accepted or revised.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-05. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-06..."
$title = "[TASK-06] Complete the CarDD Dataset Analysis Notebook"
$body = @'
## Task Description
Finish the dataset-analysis notebook and use it to inspect image counts, dimensions, class distribution, annotation quality, imbalance, missing/corrupt files and other data issues that could affect training.

## Task Details
- **Epic:** Data Preparation
- **Owner:** A
- **Priority:** Medium
- **Depends on:** TASK-01,TASK-03

## Definition of Done
The notebook runs from start to finish without manual fixes; key dataset statistics and issues are shown; recommended data actions are written in the notebook.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-06. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-07..."
$title = "[TASK-07] Execute and Validate the CarDD COCO-to-YOLO Conversion"
$body = @'
## Task Description
Run the COCO-to-YOLO conversion using the approved damage taxonomy. Validate class IDs, bounding-box normalisation and file counts, then visually inspect multiple converted labels by drawing boxes over their images.

## Task Details
- **Epic:** Data Preparation
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-01,TASK-03,TASK-06

## Definition of Done
All converted labels pass validation; no invalid class IDs or box coordinates remain; visual overlays align with the annotated damage; source and converted counts are reconciled.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-07. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-08..."
$title = "[TASK-08] Apply Cleaning Decisions to the Vehicle-Part Dataset"
$body = @'
## Task Description
Create a cleaned working copy of the vehicle-part dataset using the decisions from Task 04. Remove or correct invalid records, remap classes where required, and keep a log of every cleaning rule applied.

## Task Details
- **Epic:** Data Preparation
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-04

## Definition of Done
A cleaned dataset copy is produced without changing the raw source; validation checks pass; the cleaning/remapping rules are recorded.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-08. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-09..."
$title = "[TASK-09] Finalise Train/Validation/Test Splits and Reserve a Held-Out Evaluation Set"
$body = @'
## Task Description
Create reproducible train, validation and test manifests for the prepared datasets. Check for duplicate or related-image leakage between splits, confirm useful class coverage, and reserve a held-out set that will not be used for model tuning.

## Task Details
- **Epic:** Data Preparation
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-07,TASK-08

## Definition of Done
Split files/manifests are saved; leakage checks pass; class coverage is reviewed; the held-out evaluation set is clearly separated and marked as untouched until final evaluation.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-09. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-10..."
$title = "[TASK-10] Produce Dataset Visualisation and Class Distribution Report"
$body = @'
## Task Description
Create clear figures that explain the prepared datasets, including class counts, imbalance, example annotated images and other useful distributions. Export the figures so they can be reused in the report and presentation.

## Task Details
- **Epic:** Data Preparation
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-07,TASK-08

## Definition of Done
The required dataset charts and representative annotation examples are exported, labelled and ready to reuse in project documentation.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-10. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-11..."
$title = "[TASK-11] Write the Dataset Documentation / Data Card"
$body = @'
## Task Description
Write a data card describing each dataset's source, licence, purpose, final classes, split strategy, preprocessing/cleaning, known limitations and any relevant bias or data-quality concerns.

## Task Details
- **Epic:** Data Preparation
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-09,TASK-10

## Definition of Done
The data card is complete, matches the actual prepared datasets and splits, and includes source/licence, processing steps and limitations.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-11. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-12..."
$title = "[TASK-12] Set Up Training Environment and Experiment Tracking Convention"
$body = @'
## Task Description
Standardise how model experiments are run and recorded. Define training configuration files, random seeds, run names, folders, metrics and saved artefacts, then run a small smoke test to verify the environment.

## Task Details
- **Epic:** CV Baseline
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-02

## Definition of Done
A smoke training run completes successfully; the configuration and logging convention is documented; each run produces traceable settings, metrics and artefacts.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-12. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-13..."
$title = "[TASK-13] Train the Baseline Damage Detection Model (Experiment 1)"
$body = @'
## Task Description
Train the first damage-detection baseline using the fixed damage dataset split and agreed default configuration. Save the exact configuration, training logs, best checkpoint and validation results for later comparison.

## Task Details
- **Epic:** CV Baseline
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-09,TASK-12

## Definition of Done
Baseline training completes; best model weights, configuration and logs are saved; the baseline validation metrics are recorded in the experiment tracker.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-13. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-14..."
$title = "[TASK-14] Train the Baseline Vehicle-Part Detection Model"
$body = @'
## Task Description
Train the baseline vehicle-part detector using the cleaned part dataset and the architecture decision from the feasibility spike. Save the configuration, logs, model checkpoint and validation predictions.

## Task Details
- **Epic:** CV Baseline
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-08,TASK-12,TASK-05

## Definition of Done
The part model trains successfully; best weights and run configuration are saved; validation metrics and representative predictions are recorded.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-14. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-15..."
$title = "[TASK-15] Evaluate Baseline Models and Record Reference Metrics"
$body = @'
## Task Description
Evaluate both baseline models using the agreed evaluation script and fixed validation data. Record overall and per-class metrics such as mAP, IoU and Dice where applicable, and save the results as the reference point for improvement experiments.

## Task Details
- **Epic:** CV Baseline
- **Owner:** ALL
- **Priority:** High
- **Depends on:** TASK-13,TASK-14

## Definition of Done
A baseline evaluation table is saved with overall and per-class metrics for both models; the evaluation code and prediction outputs are reproducible.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-15. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-16..."
$title = "[TASK-16] Run Damage Model Improvement Experiment 2 (Augmentation and Hyperparameters)"
$body = @'
## Task Description
Run a controlled second damage-model experiment that changes the agreed augmentations and/or hyperparameters while keeping the data split and evaluation method fixed. Record exactly what changed and compare the result with Experiment 1.

## Task Details
- **Epic:** CV Improvement
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-15

## Definition of Done
Experiment 2 has a saved configuration, checkpoint and metrics; differences from the baseline are clearly documented and quantitatively compared.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-16. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-17..."
$title = "[TASK-17] Run Damage Model Improvement Experiment 3 (Model Size or Training Strategy)"
$body = @'
## Task Description
Run a third controlled damage-model experiment using a different model size or training strategy. Keep the same split and evaluation method so the result can be compared fairly with the previous experiments.

## Task Details
- **Epic:** CV Improvement
- **Owner:** A
- **Priority:** Low
- **Depends on:** TASK-16

## Definition of Done
Experiment 3 is completed with saved settings, checkpoint and metrics; its performance is compared against the baseline and Experiment 2.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-17. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-18..."
$title = "[TASK-18] Compare Experiments and Select the Final Production Models"
$body = @'
## Task Description
Compare the completed model experiments using accuracy, per-class behaviour, generalisation and practical considerations such as inference cost. Select the final damage and part models and freeze the exact weights/configuration for integration.

## Task Details
- **Epic:** CV Improvement
- **Owner:** A
- **Priority:** High
- **Depends on:** TASK-16,TASK-17

## Definition of Done
A comparison summary explains the model choice; the selected production model versions, weights and configurations are clearly identified and frozen.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-18. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-19..."
$title = "[TASK-19] Perform Error Analysis with Correct and Incorrect Prediction Examples"
$body = @'
## Task Description
Review final-model predictions and group the main failure types, such as missed detections, false positives, wrong classes or poor localisation. Save representative correct and incorrect examples and note likely causes or future improvements.

## Task Details
- **Epic:** CV Improvement
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-18

## Definition of Done
Major failure categories are counted or summarised; labelled example images are stored; the analysis contains concrete observations and improvement recommendations.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-19. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-20..."
$title = "[TASK-20] Evaluate the Final Models on the Held-Out Unseen Dataset"
$body = @'
## Task Description
Run the frozen final models on the reserved held-out dataset only after model selection is complete. Calculate the final overall and per-class metrics and do not tune the models using these results.

## Task Details
- **Epic:** CV Improvement
- **Owner:** ALL
- **Priority:** High
- **Depends on:** TASK-18,TASK-09

## Definition of Done
Held-out evaluation is completed once with the frozen models; final unseen metrics and prediction outputs are archived; no post-test tuning is performed.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-20. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-21..."
$title = "[TASK-21] Implement the Damage-to-Part Matching Algorithm"
$body = @'
## Task Description
Implement the logic that associates each detected damage region with the most likely detected vehicle part. Use a defined geometric rule such as overlap, centre containment or IoU, and handle no-match and ambiguous cases explicitly.

## Task Details
- **Epic:** Damage-Part Match
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-18

## Definition of Done
The matching logic is implemented as a reusable module; normal, no-match and ambiguous cases are covered by tests; sample outputs show sensible damage-to-part associations.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-21. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-22..."
$title = "[TASK-22] Define and Implement the Structured CV Output Schema"
$body = @'
## Task Description
Define a consistent JSON structure for the computer-vision output, including image information, damage detections, part detections/associations and confidence values. Implement schema generation and validation so downstream components receive predictable data.

## Task Details
- **Epic:** Damage-Part Match
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-21

## Definition of Done
A documented schema exists; real inference results validate against it; required fields, data types and empty/no-detection cases are handled consistently.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-22. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-23..."
$title = "[TASK-23] Evaluate Damage-to-Part Matching Accuracy"
$body = @'
## Task Description
Create or use a manually verified sample of at least 50 damage instances with the correct vehicle-part association. Compare the algorithm's matches with the reference labels and analyse the cases where matching fails.

## Task Details
- **Epic:** Damage-Part Match
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-21,TASK-22

## Definition of Done
Matching accuracy is calculated on 50+ verified examples; incorrect matches are reviewed and the main failure reasons are documented.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-23. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-24..."
$title = "[TASK-24] Define the LLM Role, Scope and Hallucination Constraints"
$body = @'
## Task Description
Write the rules for what the LLM may and may not say. Define which fields it can use from the structured CV output, how it should handle missing or low-confidence evidence, and which unsupported claims must be prohibited.

## Task Details
- **Epic:** LLM
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-22

## Definition of Done
A clear LLM scope/constraint specification is documented, including allowed evidence, prohibited claims and behaviour for uncertain or missing detections.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-24. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-25..."
$title = "[TASK-25] Build and Test Prompt Version 1"
$body = @'
## Task Description
Create the first production-style prompt that converts the structured CV JSON into a readable vehicle-damage assessment. Test it on a fixed set of representative inputs and save both the prompt and generated reports.

## Task Details
- **Epic:** LLM
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-24

## Definition of Done
Prompt V1 is versioned and saved; it produces reports for the agreed test inputs; all input/output examples are stored for later comparison.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-25. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-26..."
$title = "[TASK-26] Build and Test Prompt Version 2 with Hardened Constraints"
$body = @'
## Task Description
Create a second prompt with stronger grounding and safety instructions, especially for uncertainty, missing evidence and unsupported conclusions. Run it on exactly the same test inputs used for Prompt V1.

## Task Details
- **Epic:** LLM
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-25

## Definition of Done
Prompt V2 is versioned and tested on the same inputs as V1; its outputs are stored in a directly comparable format and respect the hardened constraints.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-26. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-27..."
$title = "[TASK-27] Compare Prompt Versions and Select the Production Prompt"
$body = @'
## Task Description
Score Prompt V1 and V2 using the same rubric, covering factual consistency with the CV JSON, completeness, clarity, formatting and hallucination behaviour. Select and freeze the stronger prompt for integration.

## Task Details
- **Epic:** LLM
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-26

## Definition of Done
Both prompt versions have comparable rubric scores; the selection decision is documented; the chosen production prompt is saved and versioned.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-27. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-28..."
$title = "[TASK-28] Conduct Manual LLM Output Evaluation"
$body = @'
## Task Description
Manually review a representative set of reports produced by the selected prompt. Check every claim against the structured CV input and record hallucinations, omissions, misleading wording and formatting issues.

## Task Details
- **Epic:** LLM
- **Owner:** C
- **Priority:** Medium
- **Depends on:** TASK-27

## Definition of Done
A manual evaluation table is completed; hallucination/error rates are calculated or summarised; representative issues and acceptable outputs are documented.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-28. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-29..."
$title = "[TASK-29] Build the End-to-End Inference Pipeline Module"
$body = @'
## Task Description
Connect all production components into one reusable pipeline: image input, preprocessing, damage detection, part detection, damage-to-part matching, structured JSON generation and LLM report generation.

## Task Details
- **Epic:** Integration
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-21,TASK-22,TASK-27

## Definition of Done
One documented function/module call can process a valid image and return both schema-valid CV JSON and the generated assessment report.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-29. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-30..."
$title = "[TASK-30] Integration Testing, Failure Handling and Latency Profiling"
$body = @'
## Task Description
Test the integrated pipeline on normal and failure cases, including invalid files, no detections, low-confidence results and component/API failures. Add graceful error handling and measure latency for each major pipeline stage and total inference.

## Task Details
- **Epic:** Integration
- **Owner:** B
- **Priority:** High
- **Depends on:** TASK-29

## Definition of Done
The integration test matrix passes for agreed cases; users receive controlled errors instead of raw exceptions; stage and total latency measurements are recorded.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-30. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-31..."
$title = "[TASK-31] Build the Streamlit MVP Scaffold with Image Upload and Preview"
$body = @'
## Task Description
Create the Streamlit application structure and connect it to the end-to-end pipeline. Add an image uploader with basic file validation and show the selected image before inference.

## Task Details
- **Epic:** MVP
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-29

## Definition of Done
The app launches with the documented command; supported images can be uploaded and previewed; the application can call the integrated pipeline.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-31. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-32..."
$title = "[TASK-32] Display Computer Vision Detections, Confidence Scores and Part Associations"
$body = @'
## Task Description
Add a results view that shows the computer-vision output clearly. Draw detection boxes/labels on the image and display confidence values and each damage region's matched vehicle part in a readable table or panel.

## Task Details
- **Epic:** MVP
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-31

## Definition of Done
The UI renders detection overlays, labels/confidences and damage-to-part associations that match the structured pipeline output.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-32. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-33..."
$title = "[TASK-33] Display the Generated Assessment Report with Loading and Error States"
$body = @'
## Task Description
Show the LLM-generated assessment inside the Streamlit app and add clear loading/progress and error states. Ensure pipeline failures or empty results are explained to the user without exposing raw stack traces.

## Task Details
- **Epic:** MVP
- **Owner:** C
- **Priority:** High
- **Depends on:** TASK-31,TASK-30

## Definition of Done
The report renders correctly on successful runs; loading state is visible during processing; expected failure/empty-result cases show clear user-facing messages.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-33. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-34..."
$title = "[TASK-34] Conduct an MVP Usability Pass and Harden the Demo Path"
$body = @'
## Task Description
Run the complete demo workflow using the images planned for presentation. Fix confusing UI behaviour, broken steps and obvious visual issues, and prepare backup inputs plus a fallback plan if live inference fails.

## Task Details
- **Epic:** MVP
- **Owner:** C
- **Priority:** Medium
- **Depends on:** TASK-32,TASK-33

## Definition of Done
The agreed demo images complete the workflow reliably; major usability blockers are fixed; backup images and a documented fallback demo path are ready.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-34. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-35..."
$title = "[TASK-35] Conduct Integrated End-to-End System Evaluation"
$body = @'
## Task Description
Evaluate the complete system on unseen examples from image input through final report. Combine the final CV, damage-to-part matching, LLM-quality and runtime results into one system-level evaluation.

## Task Details
- **Epic:** Evaluation
- **Owner:** ALL
- **Priority:** High
- **Depends on:** TASK-34,TASK-20,TASK-28

## Definition of Done
A consolidated evaluation scorecard/report is produced using unseen data and includes the agreed CV, matching, LLM and end-to-end performance measures.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-35. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-36..."
$title = "[TASK-36] Produce the Responsible AI, Limitations and Privacy Assessment"
$body = @'
## Task Description
Document the system's known limitations, likely biases, uncertainty risks, possible misuse and privacy considerations for uploaded vehicle images. State where human review is required and how the demo handles or should handle sensitive data.

## Task Details
- **Epic:** Documentation
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-35

## Definition of Done
Responsible-AI, limitation and privacy sections are complete, specific to the implemented system, and include clear risk-mitigation and human-oversight statements.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-36. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-37..."
$title = "[TASK-37] Produce the Final README, Architecture Diagram and Model Documentation"
$body = @'
## Task Description
Write the final project README with setup, dependencies, folder structure, data/model instructions and run commands. Add an architecture diagram showing the full data flow and document the selected models and saved artefacts.

## Task Details
- **Epic:** Documentation
- **Owner:** ALL
- **Priority:** Medium
- **Depends on:** TASK-35

## Definition of Done
A new user can follow the README to set up and run the project; the architecture diagram matches the implementation; final model versions and artefact locations are documented.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-37. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-38..."
$title = "[TASK-38] Write the Final Capstone Report"
$body = @'
## Task Description
Write the final capstone report using the completed project evidence. Include all required nine sections, methodology, experiments, evaluation results, figures, limitations and conclusions, keeping numbers consistent with the saved results.

## Task Details
- **Epic:** Documentation
- **Owner:** ALL
- **Priority:** High
- **Depends on:** TASK-35,TASK-36

## Definition of Done
All nine required report sections are present; tables/figures and metrics match project artefacts; the report is complete and ready for final review/submission.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-38. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-39..."
$title = "[TASK-39] Prepare the Final Presentation, Live Demo and Backup Demo Video"
$body = @'
## Task Description
Create the final 10–12 slide presentation, define the live-demo sequence and speaker responsibilities, rehearse the full presentation, and record a backup video that shows the working system in case the live demo fails.

## Task Details
- **Epic:** Documentation
- **Owner:** ALL
- **Priority:** High
- **Depends on:** TASK-37,TASK-38

## Definition of Done
The 10–12 slide deck is final; the team has rehearsed the talk/demo within the allowed time; a tested backup demo video is available.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-39. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Creating TASK-40..."
$title = "[TASK-40] Define the Problem Statement, Use-Case Scenario and Impact Card"
$body = @'
## Task Description
Write a concise definition of the problem the project solves, the target user and use-case flow, the expected system input/output, project scope and the practical value or impact of the proposed solution.

## Task Details
- **Epic:** Documentation
- **Owner:** C
- **Priority:** High
- **Depends on:** None

## Definition of Done
The problem statement, target user/use case and Impact Card are written, internally consistent and aligned with the implemented Qaddir system.
'@
gh issue create --repo $repo --title $title --body $body
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to create TASK-40. Stopping to avoid duplicates."
    exit 1
}

Write-Host "Done. Issues created successfully."