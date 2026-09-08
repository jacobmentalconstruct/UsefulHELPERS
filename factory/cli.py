from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True

from . import release  # noqa: E402
from .installer import AttachError, attach, uninstall, update  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="useful-helpers-builder")
    commands = parser.add_subparsers(dest="command", required=True)
    attach_parser = commands.add_parser("attach", help="attach a new .useful-helpers to a target")
    attach_parser.add_argument("target")
    update_parser = commands.add_parser("update", help="replace installed runtime payload")
    update_parser.add_argument("target")
    uninstall_parser = commands.add_parser("uninstall", help="remove an installed .useful-helpers")
    uninstall_parser.add_argument("target")
    release_parser = commands.add_parser("release", help="build or inspect a sealed release")
    release_commands = release_parser.add_subparsers(dest="release_command", required=True)
    build = release_commands.add_parser("build", help="build a sealed release archive")
    build.add_argument("--output", default="release")
    inspect = release_commands.add_parser("inspect", help="inspect a sealed release archive")
    inspect.add_argument("artifact")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "attach":
            result = attach(args.target)
        elif args.command == "update":
            result = update(args.target)
        elif args.command == "uninstall":
            result = uninstall(args.target)
        elif args.command == "release":
            if args.release_command == "build":
                result = release.build(args.output)
            else:
                result = release.inspect_archive(args.artifact)
        else:  # argparse keeps this unreachable, but the adapter still fails closed.
            raise AttachError(f"unsupported command: {args.command}")
    except (AttachError, release.ReleaseError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
