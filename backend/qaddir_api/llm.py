from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from .config import Settings, Thresholds
from .schemas import CVRecord


class PromptUnavailableError(RuntimeError):
    pass


class ReportGenerationError(RuntimeError):
    pass


class ProductionPromptLoader:
    """Loads the frozen Ruba prompt without copying or editing its content."""

    def __init__(self, path: Path, thresholds: Thresholds):
        self.path = path
        self.thresholds = thresholds

    def readiness(self) -> tuple[bool, str]:
        if not self.path.is_file():
            return False, "The frozen production prompt is not present on this branch."
        verifier = self.path.with_name("verify_production.py")
        if not verifier.is_file():
            return False, "The frozen prompt verifier is missing."
        try:
            verification = subprocess.run(
                [sys.executable, str(verifier)],
                cwd=verifier.parent,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False, "The frozen prompt integrity check could not run."
        if verification.returncode != 0:
            return False, "The frozen production prompt failed its integrity check."
        if not self.thresholds.calibrated:
            return False, "Production thresholds are not calibrated/configured."
        return True, "The frozen prompt and configured thresholds are available."

    def load_system_prompt(self) -> str:
        ready, detail = self.readiness()
        if not ready:
            raise PromptUnavailableError(detail)
        source = self.path.read_text(encoding="utf-8")
        marker = "## 1. System Prompt"
        if marker not in source:
            raise PromptUnavailableError("The production prompt has no system-prompt section.")
        body = source.split(marker, 1)[1]
        try:
            system_prompt = body.split("```text", 1)[1].split("```", 1)[0].strip()
        except IndexError as exc:
            raise PromptUnavailableError("The production system-prompt fence is malformed.") from exc
        for name, value in self.thresholds.as_prompt_values().items():
            system_prompt = system_prompt.replace(f"{{{{{name}}}}}", str(value))
        unresolved = re.findall(r"\{\{(\w+)\}\}", system_prompt)
        if unresolved:
            raise PromptUnavailableError(f"Unresolved prompt placeholders: {', '.join(unresolved)}")
        return system_prompt


class OpenAIReportGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.prompt_loader = ProductionPromptLoader(settings.prompt_path, settings.thresholds)

    def readiness(self) -> tuple[bool, str]:
        prompt_ready, prompt_detail = self.prompt_loader.readiness()
        if not prompt_ready:
            return False, prompt_detail
        if not self.settings.llm_api_key:
            return False, "OPENAI_API_KEY is not configured."
        if not self.settings.llm_model:
            return False, "QADDIR_LLM_MODEL is not configured."
        return True, "The LLM gateway is configured."

    def generate(self, record: CVRecord) -> str:
        ready, detail = self.readiness()
        if not ready:
            raise PromptUnavailableError(detail)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.llm_api_key)
            cv_json = json.dumps(record.model_dump(by_alias=True), ensure_ascii=False)
            response = client.responses.create(
                model=self.settings.llm_model,
                instructions=self.prompt_loader.load_system_prompt(),
                input=(
                    "Generate a preliminary damage report from the following structured "
                    "detection output. Use only the fields present.\n\n" + cv_json
                ),
                max_output_tokens=1000,
                store=False,
            )
            text = response.output_text.strip()
            if not text:
                raise ReportGenerationError("The LLM returned an empty report.")
            return text
        except (PromptUnavailableError, ReportGenerationError):
            raise
        except Exception as exc:
            raise ReportGenerationError("The report service could not generate a response.") from exc
