# Reference PDF Extraction

The extraction script reads the PDF text layer first and uses Arabic/English OCR only when a page has no usable text or fails the built-in quality checks.

## Setup

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Install Tesseract OCR 5 with the `ara` and `eng` language data. On Ubuntu or Google Colab:

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-ara
```

## Run

From the project root:

```bash
python scripts/extract_reference_pdf.py
```

If Tesseract is not on `PATH` in Windows, provide its executable explicitly:

```powershell
python scripts/extract_reference_pdf.py --tesseract-command "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

The script writes a new candidate Markdown file and quality report under `references/processed/`. It compares the candidate with the reviewed `_ocr.md` file but never replaces it. If a candidate already exists, the script creates a numbered candidate filename.

Review the OCR pages, right-to-left lists, and detected tables before promoting any candidate manually.

## Canonical artifacts

- Keep `references/professional_standards_vehicle_damage_assessment_ar.pdf` unchanged as the official source artifact.
- Use `references/processed/professional_standards_vehicle_damage_assessment_ocr.md` as the reviewed, searchable text.
- Use `references/processed/professional_standards_vehicle_damage_assessment_ocr_quality_report.md` to record provenance, the source hash, extraction methods, and manual-review limitations.
- Treat files containing `_candidate` as temporary review outputs. Do not index or commit them unless they are intentionally reviewed and promoted.

The extraction script records repository-relative paths for project files. If a custom source is outside the repository, only its filename is recorded, preventing user-specific paths from entering generated artifacts.

## Future LLM/RAG use

Index the reviewed Markdown rather than an unreviewed candidate. Preserve the `## Page N` boundaries so retrieved passages can be traced back to the official PDF.

Recommended metadata for each indexed chunk:

| Field | Value or source |
|---|---|
| `document_title` | `المعايير المهنية لتقييم أضرار المركبات` |
| `authority` | Saudi Authority for Accredited Valuers (Taqeem) |
| `source_url` | Official URL recorded in the reviewed text and quality report |
| `source_sha256` | SHA-256 recorded in the quality report |
| `page_number` | Parsed from the nearest `## Page N` heading |
| `section` | Nearest document heading or standards section |
| `language` | `ar` |
| `review_status` | `reviewed` |

Chunk by semantic paragraph or numbered rule while retaining the page number and section. Avoid splitting a numbered condition from its qualifying text. Retrieval responses should cite the official document and page number, and should distinguish quoted standards from model interpretation.

This reference supports retrieval and summarization; it does not replace a professional vehicle assessment or an authoritative interpretation of the standards.

## Refresh workflow

1. Preserve the current official PDF and its recorded SHA-256.
2. Run the extractor to create a new candidate and quality report.
3. Compare the candidate with the reviewed Markdown.
4. Visually review OCR pages, tables, percentages, and right-to-left lists against the PDF.
5. Promote a candidate only through an explicit human-reviewed change.
6. Rebuild the RAG index only after the reviewed artifact and provenance metadata are updated.
