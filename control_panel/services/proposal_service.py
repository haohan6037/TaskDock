from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
BRAIN_DIR = PROJECT_ROOT / "brain"
if str(BRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(BRAIN_DIR))

from proposal_manager import create_proposal, list_proposals, proposal_path, read_proposal  # noqa: E402


REQUIRED_SECTIONS = [
    "## Goal",
    "## Motivation",
    "## Proposed New Files",
    "## Proposed Modified Files",
    "## Why This Shape",
    "## Risk Level",
    "## Validation Plan",
    "## Approval",
]


@dataclass
class ProposalCheck:
    name: str
    passed: bool
    detail: str


def get_proposals() -> List[dict]:
    proposals = []
    for item in list_proposals():
        checks = validate_proposal(item["id"])
        proposals.append({**item, "quality_passed": all(check.passed for check in checks)})
    return proposals


def get_proposal(proposal_id: str) -> dict:
    content = read_proposal(proposal_id)
    path = proposal_path(proposal_id)
    checks = validate_proposal(proposal_id)
    return {
        "id": proposal_id.zfill(3),
        "path": str(path),
        "content": content,
        "checks": checks,
        "quality_passed": all(check.passed for check in checks),
    }


def section_body(content: str, section: str) -> str:
    pattern = rf"{re.escape(section)}\n\n(?P<body>.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, flags=re.S)
    return match.group("body").strip() if match else ""


def validate_proposal(proposal_id: str) -> List[ProposalCheck]:
    path = proposal_path(proposal_id)
    content = path.read_text(encoding="utf-8")
    checks = [
        ProposalCheck("filename starts with three-digit id", bool(re.match(r"^\d{3}-", path.name)), path.name),
        ProposalCheck("title is present", content.startswith("# Proposal "), "first line should be a proposal title"),
        ProposalCheck("status is present", "Status:" in content, "Status line required"),
        ProposalCheck(
            "requires approval before implementation",
            "Requires approval before implementation: yes" in content,
            "Explicit approval requirement required",
        ),
        ProposalCheck("contains no TBD", "TBD" not in content, "Proposal should be complete before review"),
    ]
    for section in REQUIRED_SECTIONS:
        body = section_body(content, section)
        checks.append(ProposalCheck(f"{section} present and non-empty", bool(body), section))
    return checks


def count_by_status() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in list_proposals():
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def create_structured_proposal(
    title: str,
    goal: str,
    motivation: str,
    new_files: str,
    modified_files: str,
    why_shape: str,
    risk_level: str,
    validation_plan: str,
) -> Path:
    path = create_proposal(title=title, motivation=motivation)
    content = f"""# Proposal {path.name.split('-', 1)[0]}: {title}

Status: proposed

Requires approval before implementation: yes

## Goal

{goal}

## Motivation

{motivation}

## Proposed New Files

{new_files}

## Proposed Modified Files

{modified_files}

## Why This Shape

{why_shape}

## Risk Level

{risk_level}

## Validation Plan

{validation_plan}

## Approval

This proposal is not approved yet.

No code should be modified until the human explicitly approves this proposal.
"""
    path.write_text(content, encoding="utf-8")
    return path
