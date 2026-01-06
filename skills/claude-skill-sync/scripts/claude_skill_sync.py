#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


DEFAULT_SOURCE = Path("~/.claude/skills").expanduser()
DEFAULT_DEST = Path("~/.codex/skills").expanduser()
OFFICIAL_PLUGIN_ROOTS = [
    Path("~/.claude/plugins/marketplaces/claude-plugins-official/plugins").expanduser(),
    Path("~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins").expanduser(),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy or sync Claude skills into Codex.",
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="Claude skills directory (default: ~/.claude/skills)",
    )
    parser.add_argument(
        "--extra-source",
        action="append",
        default=[],
        help="Additional skills directories (repeatable).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan sources for SKILL.md (useful for plugin trees).",
    )
    parser.add_argument(
        "--include-official-plugins",
        action="store_true",
        help="Include official Claude plugin skills from ~/.claude/plugins/marketplaces.",
    )
    parser.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help="Codex skills directory (default: ~/.codex/skills)",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "sync"],
        default="copy",
        help="copy: one-off import, sync: repeatable updates",
    )
    parser.add_argument(
        "--conflict",
        choices=["ask", "skip", "overwrite", "abort"],
        default="ask",
        help="How to handle existing destination skills",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without copying",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="(sync only) remove destination skills not present in source",
    )
    return parser.parse_args()


def list_skill_dirs(root: Path, recursive: bool) -> list[Path]:
    skills: list[Path] = []
    if recursive:
        for skill_file in sorted(root.rglob("SKILL.md")):
            skill_dir = skill_file.parent
            relative_parts = skill_dir.relative_to(root).parts
            if any(part.startswith(".") for part in relative_parts):
                continue
            skills.append(skill_dir)
        return skills

    for entry in sorted(root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            skills.append(entry)
    return skills


def resolve_conflict(dest_dir: Path, policy: str, dry_run: bool) -> str:
    if policy != "ask":
        return policy
    if dry_run:
        print(
            f"DRY RUN: conflict for {dest_dir.name}; defaulting to skip. "
            "Re-run with --conflict overwrite|skip|abort to preview a policy."
        )
        return "skip"

    prompt = (
        f"Conflict: {dest_dir.name} exists at {dest_dir}. "
        "Choose [o]verwrite, [s]kip, or [a]bort: "
    )
    while True:
        try:
            response = input(prompt).strip().lower()
        except EOFError:
            print(
                "No interactive input available. Re-run with "
                "--conflict overwrite|skip|abort.",
                file=sys.stderr,
            )
            return "abort"

        if response in {"o", "overwrite", "y", "yes"}:
            return "overwrite"
        if response in {"s", "skip", "", "n", "no"}:
            return "skip"
        if response in {"a", "abort", "q", "quit"}:
            return "abort"

        print("Please choose 'o', 's', or 'a'.")


def copy_skill(
    src_dir: Path,
    dest_root: Path,
    conflict_policy: str,
    dry_run: bool,
) -> str:
    dest_dir = dest_root / src_dir.name
    action = "copy"

    if dest_dir.exists():
        decision = resolve_conflict(dest_dir, conflict_policy, dry_run)
        if decision == "skip":
            return "skip"
        if decision == "abort":
            raise RuntimeError("Aborted on conflict.")
        if decision == "overwrite":
            action = "overwrite"
            if not dry_run:
                shutil.rmtree(dest_dir)

    if dry_run:
        return action

    shutil.copytree(src_dir, dest_dir)
    return action


def prune_dest(
    source_names: set[str],
    dest_root: Path,
    dry_run: bool,
) -> int:
    pruned = 0
    for dest_skill in list_skill_dirs(dest_root, recursive=False):
        if dest_skill.name in source_names:
            continue
        if dry_run:
            print(f"PRUNE: {dest_skill.name} -> {dest_skill}")
        else:
            shutil.rmtree(dest_skill)
        pruned += 1
    return pruned


def main() -> int:
    args = parse_args()
    source_root = Path(args.source).expanduser()
    dest_root = Path(args.dest).expanduser()

    if args.prune and args.mode != "sync":
        print("--prune is only valid with --mode sync.", file=sys.stderr)
        return 1

    sources: list[tuple[Path, bool]] = [(source_root, args.recursive)]
    for extra in args.extra_source:
        sources.append((Path(extra).expanduser(), args.recursive))
    if args.include_official_plugins:
        for plugin_root in OFFICIAL_PLUGIN_ROOTS:
            sources.append((plugin_root, True))

    valid_sources: list[tuple[Path, bool]] = []
    for path, recursive in sources:
        if not path.exists():
            print(f"Skipping missing source: {path}", file=sys.stderr)
            continue
        if not path.is_dir():
            print(f"Skipping non-directory source: {path}", file=sys.stderr)
            continue
        valid_sources.append((path, recursive))

    if not valid_sources:
        print("No valid sources found.", file=sys.stderr)
        return 1

    skills: list[Path] = []
    for path, recursive in valid_sources:
        skills.extend(list_skill_dirs(path, recursive=recursive))
    if not skills:
        print("No skills found in the provided sources.")
        return 0

    if not dest_root.exists():
        if args.dry_run:
            print(f"DRY RUN: would create destination {dest_root}")
        else:
            dest_root.mkdir(parents=True, exist_ok=True)

    print("Sources:")
    for path, recursive in valid_sources:
        flag = "recursive" if recursive else "direct"
        print(f"- {path} ({flag})")
    print(f"Destination: {dest_root}")
    print(f"Mode: {args.mode} | Conflict: {args.conflict} | Dry run: {args.dry_run}")
    print(f"Skills found: {len(skills)}")

    counts = {"copy": 0, "overwrite": 0, "skip": 0}
    try:
        for skill_dir in skills:
            action = copy_skill(
                skill_dir,
                dest_root,
                args.conflict,
                args.dry_run,
            )
            counts[action] += 1
            print(f"{action.upper()}: {skill_dir.name} -> {dest_root / skill_dir.name}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    pruned = 0
    if args.mode == "sync" and args.prune:
        if not dest_root.exists():
            print("DRY RUN: destination does not exist, nothing to prune.")
        else:
            pruned = prune_dest(
                {skill.name for skill in skills},
                dest_root,
                args.dry_run,
            )

    print(
        "Summary: "
        f"copied {counts['copy']}, "
        f"overwritten {counts['overwrite']}, "
        f"skipped {counts['skip']}"
        + (f", pruned {pruned}" if args.prune else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
