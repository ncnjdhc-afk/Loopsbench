#!/usr/bin/env python3
from __future__ import annotations

import argparse


def publish_allowed(
    *, event_name: str, ref_name: str, default_branch: str
) -> tuple[bool, str]:
    normalized_event = event_name.strip()
    normalized_ref = ref_name.strip()
    normalized_default = default_branch.strip()

    if normalized_event != "push":
        return (
            False,
            f"Publish is only allowed from push events on {normalized_default}; got {normalized_event}.",
        )
    if normalized_ref != normalized_default:
        return (
            False,
            f"Publish is only allowed from the default branch {normalized_default}; got {normalized_ref}.",
        )
    return True, f"Publish context accepted for {normalized_event} on {normalized_ref}."


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reject publish attempts outside the trusted default-branch context."
    )
    parser.add_argument(
        "--event-name", required=True, help="GitHub event name, for example push."
    )
    parser.add_argument(
        "--ref-name", required=True, help="Git reference name, for example main."
    )
    parser.add_argument(
        "--default-branch", default="main", help="Expected default branch name."
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    ok, message = publish_allowed(
        event_name=args.event_name,
        ref_name=args.ref_name,
        default_branch=args.default_branch,
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
