from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from nomenclator_delta.build import build_comparison
from nomenclator_delta.collect import collect_snapshot
from nomenclator_delta.validate import validate_dataset


DEFAULT_CSV_URL = (
    "https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=buscarProductos"
    "&especialidad=%25%25%25&d-4015021-e=1&6578706f7274=1%20%C2%A0"
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="nomenclator-delta")
    commands = parser.add_subparsers(dest="command", required=True)

    collect_parser = commands.add_parser("collect", help="Archive the current official CSV export")
    collect_parser.add_argument("--snapshot", required=True)
    collect_parser.add_argument("--source-root", type=Path, default=Path("sources"))
    collect_parser.add_argument("--url", default=DEFAULT_CSV_URL)

    build_parser = commands.add_parser("build", help="Build one snapshot comparison")
    build_parser.add_argument("--from", dest="from_snapshot", required=True)
    build_parser.add_argument("--to", dest="to_snapshot", required=True)
    build_parser.add_argument("--from-source", type=Path, required=True)
    build_parser.add_argument("--to-source", type=Path, required=True)
    build_parser.add_argument("--from-metadata", type=Path)
    build_parser.add_argument("--to-metadata", type=Path)
    build_parser.add_argument("--output", type=Path, default=Path("data"))
    build_parser.add_argument("--minimum-records", type=int, default=15_000)

    validate_parser = commands.add_parser("validate", help="Validate generated static data")
    validate_parser.add_argument("root", type=Path, nargs="?", default=Path("data"))

    dist_parser = commands.add_parser("dist", help="Build the deployable static directory")
    dist_parser.add_argument("--site", type=Path, default=Path("site"))
    dist_parser.add_argument("--data", type=Path, default=Path("data"))
    dist_parser.add_argument("--output", type=Path, default=Path("dist"))

    args = parser.parse_args(argv)
    if args.command == "collect":
        metadata = collect_snapshot(args.snapshot, args.source_root, args.url)
        print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.command == "build":
        metadata = build_comparison(
            args.from_source,
            args.to_source,
            args.from_snapshot,
            args.to_snapshot,
            args.output,
            from_metadata=args.from_metadata,
            to_metadata=args.to_metadata,
            minimum_records=args.minimum_records,
        )
        print(f"Built {metadata['transitions'][0]} into {args.output}")
    elif args.command == "validate":
        errors = validate_dataset(args.root)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            raise SystemExit(1)
        print(f"Validated {args.root}")
    elif args.command == "dist":
        build_dist(args.site, args.data, args.output)
        print(f"Built {args.output}")


def build_dist(site: Path, data: Path, output: Path) -> None:
    if output.resolve() in {Path("/").resolve(), Path.cwd().resolve()}:
        raise ValueError("refusing to replace a broad output directory")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(site, output)
    shutil.copytree(data, output / "data")
