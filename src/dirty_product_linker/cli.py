"""Command-line interface for versioned product-linking inference."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from dirty_product_linker.api.app import DEFAULT_CATALOG
from dirty_product_linker.api.service import LinkingService, build_runtime_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="product-linker")
    commands = parser.add_subparsers(dest="command", required=True)
    predict = commands.add_parser("predict", help="resolve one noisy product mention")
    predict.add_argument("text", help="raw customer query")
    predict.add_argument(
        "--runtime",
        choices=("full", "lexical"),
        default="full",
        help="full pipeline or lightweight lexical baseline (default: full)",
    )
    predict.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    predict.add_argument("--device", default="cpu")
    predict.add_argument(
        "--offline",
        action="store_true",
        help="load the pinned embedding model only from the local Hugging Face cache",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    service: LinkingService | None = None,
) -> int:
    """Execute a CLI command and return a process-compatible exit code."""

    args = _parser().parse_args(argv)
    if args.command == "predict":
        runtime = service or build_runtime_service(
            args.runtime,
            catalog_path=args.catalog,
            device=args.device,
            local_files_only=args.offline,
        )
        result = runtime.analyze(args.text)
        print(result.model_dump_json(indent=2))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
