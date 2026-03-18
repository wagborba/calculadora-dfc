"""Entry point for the DFC Framework CLI.

Usage:
    python -m dfc                              # interactive evaluation
    python -m dfc --compare file_a.json file_b.json  # comparison mode
"""

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="python -m dfc",
        description="Digital Friction Coefficient (DFC) Framework v1.0 - By Wagner Borba",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python -m dfc\n"
            "  python -m dfc --compare avaliacao_v1.json avaliacao_v2.json\n"
        ),
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("ARQUIVO_A", "ARQUIVO_B"),
        help="Comparar dois arquivos JSON de avaliação lado a lado.",
    )
    return parser


def main() -> None:
    """Parse arguments and dispatch to the correct mode."""
    parser = _build_parser()
    args = parser.parse_args()

    # Detect rich availability once for the whole run
    try:
        import rich  # noqa: F401
        use_rich = True
    except ImportError:
        use_rich = False

    try:
        if args.compare:
            _run_compare(args.compare, use_rich)
        else:
            _run_evaluation()
    except KeyboardInterrupt:
        print()
        print("\n  Avaliação interrompida pelo usuário. Até logo!")
        print()
        sys.exit(0)


def _run_evaluation() -> None:
    """Run the interactive evaluation flow."""
    from .cli import run_evaluation, run_export_prompt

    result = run_evaluation()
    if result is not None:
        run_export_prompt(result)


def _run_compare(paths: list[str], use_rich: bool) -> None:
    """Run the comparison mode.

    Args:
        paths: List of exactly two file path strings.
        use_rich: Whether rich rendering is available.
    """
    from .comparator import compare

    path_a = Path(paths[0])
    path_b = Path(paths[1])

    for p in (path_a, path_b):
        if not p.exists():
            print(f"\n  Erro: arquivo não encontrado: {p}\n")
            sys.exit(1)

    compare(path_a, path_b, use_rich=use_rich)


if __name__ == "__main__":
    main()
