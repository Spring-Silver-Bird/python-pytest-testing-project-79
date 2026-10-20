"""Command-line interface for the page loader."""

import argparse
import os
import sys

from page_loader.loader import download


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="page-loader",
        description="Download a web page and save it to a directory.",
    )
    parser.add_argument("url", help="URL of the page to download")
    parser.add_argument(
        "--output",
        default=os.getcwd(),
        help="existing directory to save the page into (default: cwd)",
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        filepath = download(args.url, args.output)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(filepath)


if __name__ == "__main__":
    main()
