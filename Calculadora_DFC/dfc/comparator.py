"""Side-by-side comparison of two DFC evaluation results."""

from pathlib import Path

from .exporter import load_json

# Minimum delta to consider a change significant (avoids noise from rounding)
_DELTA_THRESHOLD = 0.005


def _arrow(delta: float) -> str:
    """Return a directional arrow based on the delta value.

    Higher CF means MORE friction, so an increase is negative.

    Args:
        delta: Difference (new - old) in normalised scores.

    Returns:
        '↑' if friction increased, '↓' if decreased, '→' if stable.
    """
    if delta > _DELTA_THRESHOLD:
        return "↑"
    if delta < -_DELTA_THRESHOLD:
        return "↓"
    return "→"


def _cf_arrow(delta: float) -> str:
    """Same as _arrow but with a reminder that higher = worse."""
    return _arrow(delta)


def compare(path_a: Path, path_b: Path, use_rich: bool = False) -> None:
    """Load two JSON files and print a side-by-side comparison.

    Args:
        path_a: Path to the first (older) evaluation JSON.
        path_b: Path to the second (newer) evaluation JSON.
        use_rich: If True, attempt to render with the rich library.

    Raises:
        FileNotFoundError: If either path does not exist.
        KeyError: If the JSON structure is unexpected.
    """
    data_a = load_json(path_a)
    data_b = load_json(path_b)

    if use_rich:
        try:
            _compare_rich(data_a, data_b)
            return
        except ImportError:
            pass

    _compare_plain(data_a, data_b)


# ---------------------------------------------------------------------------
# Plain-text renderer
# ---------------------------------------------------------------------------

def _compare_plain(a: dict, b: dict) -> None:
    """Render the comparison as plain text.

    Args:
        a: Parsed dict from the first JSON file.
        b: Parsed dict from the second JSON file.
    """
    sep = "=" * 66
    print(sep)
    print("  COMPARAÇÃO DE AVALIAÇÕES — DFC Framework")
    print(sep)
    print(f"  A: {a['product_name']}  ({a['evaluated_at'][:10]})")
    print(f"  B: {b['product_name']}  ({b['evaluated_at'][:10]})")
    print()

    cf_a = a["cf"]
    cf_b = b["cf"]
    delta_cf = cf_b - cf_a
    print(f"  CF Final   A: {cf_a:.2f}  ({a['classification']})")
    print(f"  CF Final   B: {cf_b:.2f}  ({b['classification']})")
    print(f"  Delta CF   : {delta_cf:+.2f}  {_cf_arrow(delta_cf)}")
    print()

    print("-" * 66)
    header = f"  {'Dimensão':<30} {'A':>6} {'B':>6} {'Δ':>6}  {'':>2}"
    print(header)
    print("-" * 66)

    dims_b = {d["id"]: d for d in b["dimensions"]}

    for dim_a in a["dimensions"]:
        dim_b = dims_b.get(dim_a["id"])
        name = dim_a["name"]

        if dim_a["skipped"]:
            score_a_str = "SKIP"
        else:
            score_a_str = f"{dim_a['score_normalized']:.2f}"

        if dim_b is None or dim_b["skipped"]:
            score_b_str = "SKIP"
            delta_str = "  —"
            arrow = " "
        else:
            score_b = dim_b["score_normalized"]
            score_b_str = f"{score_b:.2f}"
            if dim_a["skipped"]:
                delta_str = "  —"
                arrow = " "
            else:
                delta = score_b - dim_a["score_normalized"]
                delta_str = f"{delta:+.2f}"
                arrow = _arrow(delta)

        print(f"  {name:<30} {score_a_str:>6} {score_b_str:>6} {delta_str:>6}  {arrow}")

    print("-" * 66)
    print()
    print("  ↑ = fricção aumentou   ↓ = fricção diminuiu   → = estável")
    print(sep)


# ---------------------------------------------------------------------------
# Rich renderer
# ---------------------------------------------------------------------------

def _compare_rich(a: dict, b: dict) -> None:
    """Render the comparison using the rich library.

    Args:
        a: Parsed dict from the first JSON file.
        b: Parsed dict from the second JSON file.

    Raises:
        ImportError: If rich is not installed.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.panel import Panel
    from rich.text import Text

    console = Console()

    cf_a = a["cf"]
    cf_b = b["cf"]
    delta_cf = cf_b - cf_a
    arrow = _cf_arrow(delta_cf)
    arrow_color = "red" if delta_cf > _DELTA_THRESHOLD else "green" if delta_cf < -_DELTA_THRESHOLD else "yellow"

    summary = (
        f"[bold]A:[/bold] {a['product_name']} ({a['evaluated_at'][:10]}) — "
        f"CF {cf_a:.2f} [{a['classification']}]\n"
        f"[bold]B:[/bold] {b['product_name']} ({b['evaluated_at'][:10]}) — "
        f"CF {cf_b:.2f} [{b['classification']}]\n\n"
        f"Delta CF: [{arrow_color}]{delta_cf:+.2f} {arrow}[/{arrow_color}]"
    )
    console.print(Panel(summary, title="DFC — Comparação de Avaliações", expand=False))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Dimensão", style="dim", min_width=28)
    table.add_column("A", justify="right", min_width=6)
    table.add_column("B", justify="right", min_width=6)
    table.add_column("Δ", justify="right", min_width=6)
    table.add_column("", justify="center", min_width=2)

    dims_b = {d["id"]: d for d in b["dimensions"]}

    for dim_a in a["dimensions"]:
        dim_b = dims_b.get(dim_a["id"])
        name = dim_a["name"]

        score_a_str = "SKIP" if dim_a["skipped"] else f"{dim_a['score_normalized']:.2f}"

        if dim_b is None or dim_b["skipped"]:
            score_b_str = "SKIP"
            delta_str = "—"
            arrow_cell = Text(" ")
        else:
            score_b = dim_b["score_normalized"]
            score_b_str = f"{score_b:.2f}"
            if dim_a["skipped"]:
                delta_str = "—"
                arrow_cell = Text(" ")
            else:
                delta = score_b - dim_a["score_normalized"]
                delta_str = f"{delta:+.2f}"
                ar = _arrow(delta)
                color = "red" if ar == "↑" else "green" if ar == "↓" else "yellow"
                arrow_cell = Text(ar, style=color)

        table.add_row(name, score_a_str, score_b_str, delta_str, arrow_cell)

    console.print(table)
    console.print("[dim]↑ fricção aumentou  ↓ diminuiu  → estável[/dim]")
