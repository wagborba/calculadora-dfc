"""Export evaluation results to JSON and TXT formats."""

import json
import re
from datetime import datetime
from pathlib import Path

from .calculator import EvaluationResult


def _safe_filename(product_name: str) -> str:
    """Convert a product name to a safe filename slug.

    Args:
        product_name: Raw product name string.

    Returns:
        Lowercase, hyphenated, alphanumeric slug.
    """
    slug = product_name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "produto"


def _base_path(result: EvaluationResult, output_dir: Path) -> Path:
    """Return the base file path (without extension) for exports.

    Args:
        result: The evaluation result containing product name and date.
        output_dir: Directory where files will be written.

    Returns:
        A Path object with the base name (no extension).
    """
    slug = _safe_filename(result.product_name)
    date_str = result.evaluated_at.strftime("%Y-%m-%d")
    return output_dir / f"dfc_{slug}_{date_str}"


def export_json(result: EvaluationResult, output_dir: Path = Path(".")) -> Path:
    """Export evaluation result to a structured JSON file.

    Args:
        result: The evaluation result to export.
        output_dir: Directory where the file will be written.

    Returns:
        Path to the written JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _base_path(result, output_dir).with_suffix(".json")

    payload: dict = {
        "product_name": result.product_name,
        "evaluated_at": result.evaluated_at.isoformat(),
        "cf": round(result.cf, 4),
        "classification": result.classification,
        "dimensions": [],
    }

    for dr in result.dimensions:
        payload["dimensions"].append(
            {
                "id": dr.dimension_id,
                "name": dr.dimension_name,
                "weight": dr.weight,
                "skipped": dr.skipped,
                "score_normalized": round(dr.score_normalized, 4),
                "scores": dr.scores,
            }
        )

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return path


def export_txt(result: EvaluationResult, output_dir: Path = Path(".")) -> Path:
    """Export evaluation result to a human-readable TXT report.

    The format is suitable for pasting into Notion, Confluence, or e-mail.

    Args:
        result: The evaluation result to export.
        output_dir: Directory where the file will be written.

    Returns:
        Path to the written TXT file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _base_path(result, output_dir).with_suffix(".txt")

    lines: list[str] = []
    sep = "=" * 54

    lines += [
        sep,
        "RELATÓRIO — DIGITAL FRICTION COEFFICIENT (DFC)",
        sep,
        f"Produto : {result.product_name}",
        f"Data    : {result.evaluated_at.strftime('%d/%m/%Y %H:%M')}",
        "",
        f"CF Final       : {result.cf:.2f}",
        f"Classificação  : {result.classification}",
        "",
    ]

    # Visual bar (40-char width)
    bar_width = 40
    filled = round(result.cf * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    lines += [f"  [{bar}] {result.cf * 100:.0f}%", ""]

    lines += ["-" * 54, "BREAKDOWN POR DIMENSÃO", "-" * 54]

    for dr in result.dimensions:
        status = "PULADA" if dr.skipped else f"{dr.score_normalized:.2f}"
        answered = len(dr.scores)
        lines.append(
            f"  {dr.dimension_name:<32} {status:>6}  (peso {dr.weight:.0%})"
        )
        if not dr.skipped and dr.scores:
            lines.append(f"    Parâmetros avaliados: {answered}")

    lines += ["", "-" * 54, "NOTAS POR PARÂMETRO", "-" * 54]

    for dr in result.dimensions:
        if dr.skipped:
            lines.append(f"\n[{dr.dimension_name}] — dimensão pulada")
            continue
        if not dr.scores:
            lines.append(f"\n[{dr.dimension_name}] — nenhum parâmetro avaliado")
            continue
        lines.append(f"\n[{dr.dimension_name}]")
        for param_id, score in dr.scores.items():
            lines.append(f"  {param_id:<30} {score}/5")

    lines += [
        "",
        sep,
        "Gerado por DFC Framework v1.0 - By Wagner Borba",
        sep,
    ]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    return path


def load_json(path: Path) -> dict:
    """Load a previously exported JSON evaluation file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dictionary with all evaluation data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
