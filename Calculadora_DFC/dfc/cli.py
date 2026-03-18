"""Interactive CLI interface for the DFC Framework."""

import sys
from datetime import datetime

from .calculator import build_evaluation, EvaluationResult
from .data import DIMENSIONS, Dimension, Parameter
from .exporter import export_json, export_txt

# ---------------------------------------------------------------------------
# Colour / rich helpers
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.text import Text
    from rich.rule import Rule

    _RICH = True
    _console = Console()
except ImportError:
    _RICH = False
    _console = None  # type: ignore[assignment]


def _print(msg: str = "") -> None:
    """Print a message, using rich markup when available.

    Args:
        msg: Message string (may contain rich markup).
    """
    if _RICH:
        _console.print(msg)
    else:
        import re
        clean = re.sub(r"\[/?[^\]]+\]", "", msg)
        print(clean)


def _rule(title: str = "") -> None:
    """Print a horizontal rule with an optional centred title.

    Args:
        title: Optional text to embed in the rule.
    """
    if _RICH:
        _console.rule(title)
    else:
        if title:
            pad = max(0, (54 - len(title) - 2) // 2)
            print("─" * pad + f" {title} " + "─" * pad)
        else:
            print("─" * 54)


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _ask(prompt: str) -> str:
    """Read a line of user input, handling EOF gracefully.

    Args:
        prompt: Text displayed before the cursor.

    Returns:
        Stripped user input (may be empty string).
    """
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _ask_score(param_label: str) -> int | None:
    """Prompt the user for a score (1–5) or Enter to skip.

    Args:
        param_label: Label shown in the input prompt.

    Returns:
        Integer 1–5, or None if the user pressed Enter to skip.
    """
    while True:
        raw = _ask(f"        Nota (1–5) ou Enter para pular: ")
        if raw == "":
            return None
        if raw in {"1", "2", "3", "4", "5"}:
            return int(raw)
        _print(f"        [yellow]Entrada inválida.[/yellow] Digite um número de 1 a 5, ou pressione Enter para pular.")


def _ask_yes_no(prompt: str) -> bool:
    """Ask a yes/no question and return True for 'yes'.

    Args:
        prompt: Question text.

    Returns:
        True if the user answered yes.
    """
    while True:
        raw = _ask(f"{prompt} (s/n): ").lower()
        if raw in {"s", "sim", "y", "yes"}:
            return True
        if raw in {"n", "nao", "não", "no"}:
            return False
        _print("        [yellow]Digite 's' para sim ou 'n' para não.[/yellow]")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _progress_bar(value: float, width: int = 40) -> str:
    """Build a text progress bar.

    Args:
        value: Float between 0.0 and 1.0.
        width: Total bar character width.

    Returns:
        A string like '[████░░░░░░] 45%'.
    """
    filled = round(value * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {value * 100:.0f}%"


def _show_header(product_name: str, now: datetime) -> None:
    """Display the application header.

    Args:
        product_name: Name of the product being evaluated.
        now: Timestamp of the evaluation session.
    """
    date_str = now.strftime("%Y-%m-%d %H:%M")
    if _RICH:
        _console.print(
            Panel(
                f"[bold cyan]Digital Friction Coefficient Framework v1.0 - By Wagner Borba[/bold cyan]\n"
                f"[dim]{'=' * 44}[/dim]\n"
                f"Produto avaliado: [bold]{product_name}[/bold]\n"
                f"Data: {date_str}",
                expand=False,
            )
        )
    else:
        print()
        print("  Digital Friction Coefficient Framework v1.0 - By Wagner Borba")
        print("  " + "=" * 44)
        print(f"  Produto avaliado: {product_name}")
        print(f"  Data: {date_str}")
        print()


def _show_dimension_header(dim: Dimension, index: int, total: int) -> None:
    """Display the header for a dimension.

    Args:
        dim: The Dimension being introduced.
        index: 1-based position of this dimension.
        total: Total number of dimensions.
    """
    title = f"DIMENSÃO {index}/{total} — {dim.name} (peso: {dim.weight:.0%})"
    _rule(title)


def _show_parameter(param: Parameter, index: int, total: int) -> None:
    """Display a parameter name and description before prompting for a score.

    Args:
        param: The Parameter being evaluated.
        index: 1-based position within the current dimension.
        total: Total number of parameters in the dimension.
    """
    _print(f"    [bold][{index}/{total}] {param.name}[/bold]")
    _print(f"          [dim]{param.description}[/dim]")


def _show_results(result: EvaluationResult) -> None:
    """Display the final evaluation results.

    Args:
        result: The computed EvaluationResult.
    """
    _rule()
    _print()

    cf_pct = result.cf * 100
    bar = _progress_bar(result.cf)

    if _RICH:
        color = _cf_color(result.cf)
        _console.print(
            Panel(
                f"[bold]CF Final:[/bold] [{color}]{result.cf:.2f}[/{color}]  "
                f"([bold]{result.classification}[/bold])\n\n"
                f"  {bar}",
                title="Resultado",
                expand=False,
            )
        )
    else:
        print()
        print(f"  CF Final : {result.cf:.2f}  ({result.classification})")
        print(f"  {bar}")
        print()

    # Breakdown table
    _rule("Breakdown por Dimensão")
    if _RICH:
        table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
        table.add_column("Dimensão", min_width=28)
        table.add_column("Score", justify="right", min_width=6)
        table.add_column("Peso", justify="right", min_width=5)
        table.add_column("Avaliados", justify="right", min_width=9)

        for dr in result.dimensions:
            if dr.skipped:
                table.add_row(dr.dimension_name, "[dim]SKIP[/dim]", f"{dr.weight:.0%}", "—")
            else:
                color = _cf_color(dr.score_normalized)
                table.add_row(
                    dr.dimension_name,
                    f"[{color}]{dr.score_normalized:.2f}[/{color}]",
                    f"{dr.weight:.0%}",
                    str(len(dr.scores)),
                )
        _console.print(table)
    else:
        print(f"  {'Dimensão':<30} {'Score':>6}  {'Peso':>5}  {'Params':>6}")
        print("  " + "-" * 52)
        for dr in result.dimensions:
            score_str = "SKIP" if dr.skipped else f"{dr.score_normalized:.2f}"
            params_str = "—" if dr.skipped else str(len(dr.scores))
            print(f"  {dr.dimension_name:<30} {score_str:>6}  {dr.weight:.0%}  {params_str:>6}")
        print()


def _cf_color(value: float) -> str:
    """Return a rich colour name based on a normalised friction value.

    Args:
        value: Score between 0.0 and 1.0.

    Returns:
        A rich colour name string.
    """
    if value < 0.20:
        return "bright_green"
    if value < 0.40:
        return "green"
    if value < 0.60:
        return "yellow"
    if value < 0.80:
        return "orange3"
    return "red"


# ---------------------------------------------------------------------------
# Main interactive flow
# ---------------------------------------------------------------------------

def run_evaluation() -> EvaluationResult | None:
    """Run the full interactive evaluation session.

    Returns:
        The computed EvaluationResult, or None if the user interrupted.
    """
    now = datetime.now()

    print()
    product_name = _ask("  Produto avaliado: ").strip()
    if not product_name:
        product_name = "Produto"

    _show_header(product_name, now)

    raw_scores: dict[str, dict[str, int]] = {}
    skipped_dims: set[str] = set()

    for dim_idx, dim in enumerate(DIMENSIONS, start=1):
        print()
        _show_dimension_header(dim, dim_idx, len(DIMENSIONS))
        print()

        skip_dim = _ask_yes_no(f"  Pular dimensão '{dim.name}' inteira?")
        if skip_dim:
            skipped_dims.add(dim.id)
            _print(f"  [dim]→ Dimensão pulada.[/dim]")
            continue

        dim_scores: dict[str, int] = {}
        print()

        for param_idx, param in enumerate(dim.parameters, start=1):
            _show_parameter(param, param_idx, len(dim.parameters))
            score = _ask_score(param.name)
            if score is not None:
                dim_scores[param.id] = score
                _print(f"        [dim]→ Nota {score} registrada.[/dim]")
            else:
                _print(f"        [dim]→ Parâmetro pulado.[/dim]")
            print()

        raw_scores[dim.id] = dim_scores

    result = build_evaluation(
        product_name=product_name,
        raw_scores=raw_scores,
        skipped_dimensions=skipped_dims,
        evaluated_at=now,
    )

    print()
    _show_results(result)
    return result


def run_export_prompt(result: EvaluationResult) -> None:
    """Prompt the user to export results and handle the export.

    Args:
        result: The evaluation result to potentially export.
    """
    from pathlib import Path

    print()
    _rule("Exportar Resultados")
    print()

    if _ask_yes_no("  Exportar resultado como JSON?"):
        path = export_json(result, Path("."))
        _print(f"  [green]✔[/green] JSON salvo em: [bold]{path}[/bold]")

    if _ask_yes_no("  Exportar resultado como TXT (relatório)?"):
        path = export_txt(result, Path("."))
        _print(f"  [green]✔[/green] TXT salvo em: [bold]{path}[/bold]")

    print()
