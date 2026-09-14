"""Extract a reference PDF to searchable Markdown with selective OCR.

The script uses the PDF text layer when it is present and readable. It renders
and OCRs only pages whose text layer is missing or fails simple quality checks.
Candidate outputs are written beside the reviewed files and are never promoted
or used to replace them automatically.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PDF = (
    PROJECT_ROOT
    / "references"
    / "professional_standards_vehicle_damage_assessment_ar.pdf"
)
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / "references" / "processed"
DEFAULT_REVIEWED_MARKDOWN = (
    DEFAULT_OUTPUT_DIRECTORY
    / "professional_standards_vehicle_damage_assessment_ocr.md"
)
DEFAULT_SOURCE_URL = (
    "https://taqeem.gov.sa/web/content/portal.library/266/"
    "attachment_ar?download=false"
)
DEFAULT_DOWNLOAD_DATE = "2026-09-09"
DEFAULT_DOCUMENT_TITLE = "المعايير المهنية لتقييم أضرار المركبات"


def portable_path(file_path: Path) -> str:
    """Return a stable path without recording a user-specific absolute path."""
    resolved_path = file_path.resolve()
    try:
        return resolved_path.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved_path.name


@dataclass
class PageResult:
    page_number: int
    selectable_text: bool
    method: str
    direct_character_count: int
    output_character_count: int
    quality_notes: list[str]
    possible_table: bool
    text: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a PDF to candidate Markdown, use OCR only on low-quality "
            "pages, and compare the candidate with the reviewed text."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_PDF,
        help="Source PDF path.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help="Directory for candidate Markdown and its quality report.",
    )
    parser.add_argument(
        "--reviewed-markdown",
        type=Path,
        default=DEFAULT_REVIEWED_MARKDOWN,
        help="Existing reviewed Markdown used only for comparison.",
    )
    parser.add_argument(
        "--source-url",
        default=DEFAULT_SOURCE_URL,
        help="Official source URL recorded in the outputs.",
    )
    parser.add_argument(
        "--download-date",
        default=DEFAULT_DOWNLOAD_DATE,
        help="Source download date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--document-title",
        default=DEFAULT_DOCUMENT_TITLE,
        help="Document title written at the top of the Markdown file.",
    )
    parser.add_argument(
        "--ocr-languages",
        default="ara+eng",
        help="Tesseract language codes. Default: ara+eng.",
    )
    parser.add_argument(
        "--ocr-dpi",
        type=int,
        default=300,
        help="Resolution used only for pages that require OCR. Default: 300.",
    )
    parser.add_argument(
        "--tesseract-command",
        type=Path,
        help="Optional full path to the Tesseract executable.",
    )
    parser.add_argument(
        "--minimum-text-characters",
        type=int,
        default=80,
        help="Minimum non-whitespace characters for a reliable text layer.",
    )
    parser.add_argument(
        "--maximum-tatweel-ratio",
        type=float,
        default=0.02,
        help="Maximum Arabic tatweel ratio accepted in direct text.",
    )
    return parser.parse_args()


def validate_arguments(arguments: argparse.Namespace) -> None:
    source_path = arguments.source.resolve()
    if not source_path.is_file():
        raise ValueError(f"Source PDF was not found: {source_path}")
    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Source file must be a PDF: {source_path}")

    try:
        date.fromisoformat(arguments.download_date)
    except ValueError as error:
        raise ValueError("Download date must use YYYY-MM-DD format.") from error

    if arguments.ocr_dpi < 150:
        raise ValueError("OCR DPI must be at least 150.")
    if arguments.minimum_text_characters < 1:
        raise ValueError("Minimum text characters must be greater than zero.")
    if not 0 <= arguments.maximum_tatweel_ratio <= 1:
        raise ValueError("Maximum tatweel ratio must be between 0 and 1.")

    reviewed_path = arguments.reviewed_markdown.resolve()
    if source_path == reviewed_path:
        raise ValueError("The source PDF and reviewed Markdown paths must differ.")


def import_pdf_dependencies():
    try:
        import fitz
        import pytesseract
        from PIL import Image, ImageStat
        from pypdf import PdfReader
    except ImportError as error:
        missing_package = error.name or "a required PDF package"
        raise ValueError(
            f"Missing dependency: {missing_package}. Install requirements.txt first."
        ) from error

    return fitz, pytesseract, Image, ImageStat, PdfReader


def count_visible_characters(text: str) -> int:
    return sum(1 for character in text if not character.isspace())


def clean_extracted_text(text: str) -> str:
    clean_lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]

    compact_lines = []
    previous_line_was_blank = False
    for line in clean_lines:
        line_is_blank = not line.strip()
        if line_is_blank and previous_line_was_blank:
            continue
        compact_lines.append(line)
        previous_line_was_blank = line_is_blank

    return "\n".join(compact_lines).strip()


def evaluate_direct_text(
    text: str,
    minimum_text_characters: int,
    maximum_tatweel_ratio: float,
) -> list[str]:
    quality_notes = []
    visible_character_count = count_visible_characters(text)

    if visible_character_count < minimum_text_characters:
        quality_notes.append(
            f"only {visible_character_count} non-whitespace characters"
        )

    if "\ufffd" in text:
        quality_notes.append("contains Unicode replacement characters")

    control_characters = []
    for character in text:
        if character in "\n\r\t":
            continue
        if unicodedata.category(character).startswith("C"):
            control_characters.append(character)
    if control_characters:
        quality_notes.append("contains unexpected control characters")

    arabic_character_count = 0
    for character in text:
        if "ARABIC" in unicodedata.name(character, ""):
            arabic_character_count += 1

    if arabic_character_count:
        tatweel_ratio = text.count("ـ") / arabic_character_count
        if tatweel_ratio > maximum_tatweel_ratio:
            quality_notes.append(
                f"Arabic tatweel ratio is {tatweel_ratio:.3f}, suggesting malformed glyphs"
            )

    return quality_notes


def configure_tesseract(pytesseract_module, command_path: Path | None) -> None:
    if command_path:
        resolved_command = command_path.resolve()
        if not resolved_command.is_file():
            raise ValueError(f"Tesseract executable was not found: {resolved_command}")
        pytesseract_module.pytesseract.tesseract_cmd = str(resolved_command)
        return

    if shutil.which("tesseract") is None:
        raise ValueError(
            "Tesseract was not found. Install Tesseract with Arabic and English "
            "language data, or pass --tesseract-command with its full path."
        )


def validate_ocr_languages(pytesseract_module, requested_languages: str) -> None:
    available_languages = set(pytesseract_module.get_languages(config=""))
    required_languages = set(requested_languages.split("+"))
    missing_languages = sorted(required_languages - available_languages)

    if missing_languages:
        missing_list = ", ".join(missing_languages)
        raise ValueError(
            f"Missing Tesseract language data: {missing_list}. "
            "Install both Arabic (ara) and English (eng) data."
        )


def render_page_as_image(fitz_page, image_module, dpi: int):
    pixmap = fitz_page.get_pixmap(dpi=dpi, alpha=False)
    return image_module.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def image_is_blank(image, image_stat_module) -> bool:
    grayscale_image = image.convert("L")
    statistics = image_stat_module.Stat(grayscale_image)
    mean_brightness = statistics.mean[0]
    brightness_deviation = statistics.stddev[0]
    return mean_brightness > 250 and brightness_deviation < 2


def run_page_ocr(
    image,
    pytesseract_module,
    languages: str,
) -> str:
    ocr_text = pytesseract_module.image_to_string(
        image,
        lang=languages,
        config="--psm 3",
    )
    return clean_extracted_text(ocr_text)


def page_may_contain_table(fitz_page) -> bool:
    find_tables = getattr(fitz_page, "find_tables", None)
    if find_tables is None:
        return False

    try:
        detected_tables = find_tables()
    except (ValueError, RuntimeError):
        return False

    return bool(getattr(detected_tables, "tables", []))


def extract_pages(arguments: argparse.Namespace) -> tuple[list[PageResult], int]:
    fitz, pytesseract, Image, ImageStat, PdfReader = import_pdf_dependencies()

    source_path = arguments.source.resolve()
    direct_reader = PdfReader(source_path)
    rendered_document = fitz.open(source_path)

    if len(direct_reader.pages) != rendered_document.page_count:
        raise ValueError("PDF readers returned different page counts.")

    page_results = []
    ocr_is_configured = False

    for page_index, direct_page in enumerate(direct_reader.pages):
        page_number = page_index + 1
        direct_text = clean_extracted_text(direct_page.extract_text() or "")
        direct_character_count = count_visible_characters(direct_text)
        quality_notes = evaluate_direct_text(
            direct_text,
            arguments.minimum_text_characters,
            arguments.maximum_tatweel_ratio,
        )

        rendered_page = rendered_document[page_index]
        possible_table = page_may_contain_table(rendered_page)

        if not quality_notes:
            output_text = direct_text
            method = "direct"
        else:
            if not ocr_is_configured:
                configure_tesseract(pytesseract, arguments.tesseract_command)
                validate_ocr_languages(pytesseract, arguments.ocr_languages)
                ocr_is_configured = True

            page_image = render_page_as_image(rendered_page, Image, arguments.ocr_dpi)
            output_text = run_page_ocr(
                page_image,
                pytesseract,
                arguments.ocr_languages,
            )
            method = "ocr"

            if not output_text and image_is_blank(page_image, ImageStat):
                quality_notes.append("rendered page appears blank")
                method = "blank"
            elif count_visible_characters(output_text) < 10:
                output_text = "[unclear]"
                quality_notes.append("OCR output remained unreadable")

        page_results.append(
            PageResult(
                page_number=page_number,
                selectable_text=bool(direct_text),
                method=method,
                direct_character_count=direct_character_count,
                output_character_count=count_visible_characters(output_text),
                quality_notes=quality_notes,
                possible_table=possible_table,
                text=output_text,
            )
        )

    rendered_document.close()
    return page_results, len(direct_reader.pages)


def make_candidate_paths(output_directory: Path, source_path: Path) -> tuple[Path, Path]:
    base_name = source_path.stem
    if base_name.endswith("_ar"):
        base_name = base_name[:-3]

    candidate_number = 1
    while True:
        suffix = "_candidate" if candidate_number == 1 else f"_candidate_{candidate_number}"
        markdown_path = output_directory / f"{base_name}{suffix}_ocr.md"
        report_path = output_directory / f"{base_name}{suffix}_ocr_quality_report.md"
        if not markdown_path.exists() and not report_path.exists():
            return markdown_path, report_path
        candidate_number += 1


def build_markdown(
    arguments: argparse.Namespace,
    page_results: list[PageResult],
    page_count: int,
) -> str:
    source_path = arguments.source.resolve()
    lines = [
        f"# {arguments.document_title}",
        "",
        f"- Official source URL: {arguments.source_url}",
        f"- Download date: {arguments.download_date}",
        f"- Extraction date: {date.today().isoformat()}",
        f"- Source file: `{portable_path(source_path)}`",
        "- File type: PDF",
        f"- Page count: {page_count}",
        "",
    ]

    for page_result in page_results:
        lines.append(f"## Page {page_result.page_number}")
        lines.append("")
        if page_result.text:
            lines.append(page_result.text)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file_stream:
        for chunk in iter(lambda: file_stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def compare_with_reviewed(candidate_text: str, reviewed_path: Path) -> dict[str, object]:
    if not reviewed_path.is_file():
        return {
            "available": False,
            "reviewed_path": reviewed_path,
        }

    reviewed_text = reviewed_path.read_text(encoding="utf-8")
    candidate_lines = candidate_text.splitlines()
    reviewed_lines = reviewed_text.splitlines()
    similarity = difflib.SequenceMatcher(None, reviewed_lines, candidate_lines).ratio()

    added_lines = 0
    removed_lines = 0
    for difference in difflib.ndiff(reviewed_lines, candidate_lines):
        if difference.startswith("+ "):
            added_lines += 1
        elif difference.startswith("- "):
            removed_lines += 1

    return {
        "available": True,
        "reviewed_path": reviewed_path,
        "exact_match": reviewed_text == candidate_text,
        "similarity": similarity,
        "added_lines": added_lines,
        "removed_lines": removed_lines,
    }


def format_page_list(page_numbers: list[int]) -> str:
    if not page_numbers:
        return "None"
    return ", ".join(str(page_number) for page_number in page_numbers)


def build_quality_report(
    arguments: argparse.Namespace,
    markdown_path: Path,
    candidate_text: str,
    page_results: list[PageResult],
    comparison: dict[str, object],
) -> str:
    source_path = arguments.source.resolve()
    lines = [
        "# OCR Quality Report",
        "",
        "## Source",
        "",
        f"- Source file: `{portable_path(source_path)}`",
        "- File type: PDF",
        f"- Page count: {len(page_results)}",
        f"- Official source URL: {arguments.source_url}",
        f"- Download date: {arguments.download_date}",
        f"- Extraction date: {date.today().isoformat()}",
        f"- Source SHA-256: `{calculate_sha256(source_path)}`",
        f"- Candidate Markdown: `{portable_path(markdown_path)}`",
        "",
        "## Page-level extraction",
        "",
        "| Page | Selectable text | Method | Direct characters | Output characters | Notes |",
        "|---:|:---:|---|---:|---:|---|",
    ]

    for page_result in page_results:
        notes = "; ".join(page_result.quality_notes) or "Direct text passed quality checks"
        if page_result.possible_table:
            notes += "; possible table requires visual review"
        notes = notes.replace("|", "\\|")
        selectable_text = "Yes" if page_result.selectable_text else "No"
        lines.append(
            f"| {page_result.page_number} | {selectable_text} | "
            f"{page_result.method} | {page_result.direct_character_count} | "
            f"{page_result.output_character_count} | {notes} |"
        )

    direct_pages = [page.page_number for page in page_results if page.method == "direct"]
    ocr_pages = [page.page_number for page in page_results if page.method == "ocr"]
    unclear_pages = [page.page_number for page in page_results if "[unclear]" in page.text]
    table_pages = [page.page_number for page in page_results if page.possible_table]

    lines.extend(
        [
            "",
            "## Quality summary",
            "",
            f"- Pages extracted directly: {format_page_list(direct_pages)}",
            f"- Pages processed using OCR: {format_page_list(ocr_pages)}",
            f"- Pages with unclear content: {format_page_list(unclear_pages)}",
            f"- Possible tables requiring manual review: {format_page_list(table_pages)}",
            "- OCR languages: " + arguments.ocr_languages,
            "",
            "## Comparison with reviewed Markdown",
            "",
        ]
    )

    if comparison["available"]:
        lines.extend(
            [
                f"- Reviewed file: `{portable_path(Path(comparison['reviewed_path']))}`",
                f"- Exact match: {comparison['exact_match']}",
                f"- Line similarity: {comparison['similarity']:.2%}",
                f"- Candidate-only lines: {comparison['added_lines']}",
                f"- Reviewed-only lines: {comparison['removed_lines']}",
                "- The reviewed file was not modified.",
            ]
        )
    else:
        lines.extend(
            [
                f"- Reviewed file not found: `{portable_path(Path(comparison['reviewed_path']))}`",
                "- No existing file was modified.",
            ]
        )

    candidate_hash = hashlib.sha256(candidate_text.encode("utf-8")).hexdigest().upper()
    lines.extend(
        [
            "",
            f"- Candidate text SHA-256: `{candidate_hash}`",
            "- Visually inspect OCR pages and possible tables before promoting this candidate.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    arguments = parse_arguments()
    validate_arguments(arguments)

    output_directory = arguments.output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    page_results, page_count = extract_pages(arguments)
    candidate_markdown = build_markdown(arguments, page_results, page_count)
    markdown_path, report_path = make_candidate_paths(
        output_directory,
        arguments.source.resolve(),
    )

    comparison = compare_with_reviewed(
        candidate_markdown,
        arguments.reviewed_markdown.resolve(),
    )
    quality_report = build_quality_report(
        arguments,
        markdown_path,
        candidate_markdown,
        page_results,
        comparison,
    )

    markdown_path.write_text(candidate_markdown, encoding="utf-8")
    report_path.write_text(quality_report, encoding="utf-8")

    print(f"Candidate Markdown: {markdown_path}")
    print(f"Quality report: {report_path}")
    if comparison["available"]:
        print(
            "Compared with reviewed Markdown: "
            f"{comparison['similarity']:.2%} line similarity"
        )
    else:
        print("Reviewed Markdown was not found; no comparison was made.")
    print("Existing reviewed files were not modified.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
