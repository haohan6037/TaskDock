import argparse
import re
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROPOSALS_DIR = PROJECT_ROOT / "memory" / "proposals"
TEMPLATE_FILE = PROPOSALS_DIR / "TEMPLATE.md"


def normalize_proposal_id(proposal_id: str) -> str:
    match = re.search(r"\d+", proposal_id)
    if not match:
        raise ValueError(f"Invalid proposal id: {proposal_id}")
    return match.group(0).zfill(3)


def proposal_path(proposal_id: str) -> Path:
    normalized = normalize_proposal_id(proposal_id)
    matches = sorted(PROPOSALS_DIR.glob(f"{normalized}-*.md"))
    if not matches:
        raise FileNotFoundError(f"No proposal found for id {normalized}")
    return matches[0]


def read_proposal(proposal_id: str) -> str:
    return proposal_path(proposal_id).read_text(encoding="utf-8")


def proposal_status(proposal_id: str) -> str:
    content = read_proposal(proposal_id)
    for line in content.splitlines():
        if line.lower().startswith("status:"):
            return line.split(":", 1)[1].strip().lower()
    return "unknown"


def is_proposal_approved(proposal_id: str) -> bool:
    return proposal_status(proposal_id) in {"approved", "implemented"}


def list_proposals() -> list[dict]:
    proposals = []
    for path in sorted(PROPOSALS_DIR.glob("[0-9][0-9][0-9]-*.md")):
        proposal_id = path.name.split("-", 1)[0]
        status = "unknown"
        title = path.stem
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line.removeprefix("# ").strip()
            if line.lower().startswith("status:"):
                status = line.split(":", 1)[1].strip().lower()
        proposals.append({"id": proposal_id, "status": status, "title": title, "path": str(path)})
    return proposals


def next_proposal_id() -> str:
    existing = [int(item["id"]) for item in list_proposals()]
    return str(max(existing, default=0) + 1).zfill(3)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return slug or "proposal"


def create_proposal(title: str, motivation: str) -> Path:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    proposal_id = next_proposal_id()
    path = PROPOSALS_DIR / f"{proposal_id}-{slugify(title)}.md"
    today = date.today().isoformat()

    content = f"""# Proposal {proposal_id}: {title}

Status: proposed

Proposed at: {today}

Requires approval before implementation: yes

## Goal

{title}

## Motivation

{motivation}

## Proposed New Files

- TBD

## Proposed Modified Files

- TBD

## Why This Shape

TBD

## Risk Level

TBD

## Validation Plan

TBD

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves this proposal.
"""
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage OpenClaw Brain evolution proposals.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List proposals.")

    read_parser = subparsers.add_parser("read", help="Read a proposal by id.")
    read_parser.add_argument("proposal_id")

    status_parser = subparsers.add_parser("status", help="Print a proposal status by id.")
    status_parser.add_argument("proposal_id")

    create_parser = subparsers.add_parser("create", help="Create a proposal draft.")
    create_parser.add_argument("title")
    create_parser.add_argument("motivation")

    args = parser.parse_args()

    if args.command == "list":
        for item in list_proposals():
            print(f"{item['id']}\t{item['status']}\t{item['title']}\t{item['path']}")
        return 0

    if args.command == "read":
        print(read_proposal(args.proposal_id))
        return 0

    if args.command == "status":
        print(proposal_status(args.proposal_id))
        return 0

    if args.command == "create":
        path = create_proposal(args.title, args.motivation)
        print(path)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
