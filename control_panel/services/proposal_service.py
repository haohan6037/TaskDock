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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "worker"


def next_worker_proposal_id() -> str:
    existing = []
    for path in (PROJECT_ROOT / "memory" / "proposals").glob("[0-9][0-9][0-9]-*.md"):
        try:
            existing.append(int(path.name.split("-", 1)[0]))
        except ValueError:
            continue
    return str(max(existing, default=0) + 1).zfill(3)


def create_worker_proposal(data: dict[str, str]) -> Path:
    proposals_dir = PROJECT_ROOT / "memory" / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    worker_name = slugify(data.get("worker_name", ""))
    worker_type = data.get("worker_type", "").strip() or worker_name.replace("-worker", "")
    port = data.get("port", "").strip()
    purpose = data.get("purpose", "").strip()
    skills = [skill.strip() for skill in data.get("skills", "").split(",") if skill.strip()]
    risk_level = data.get("risk_level", "").strip() or "low"
    proposal_id = next_worker_proposal_id()
    path = proposals_dir / f"{proposal_id}-add-{worker_name}.md"
    skills_text = "\n".join(f"- {skill}" for skill in skills) or "- No skills provided."

    content = f"""# Proposal {proposal_id}: Add {worker_name}

Status: proposed

Requires approval before implementation: yes

## Goal

Add a future `{worker_name}` Docker worker proposal for `{worker_type}` tasks.

## Motivation

Purpose: {purpose or "No purpose provided."}

## Proposed New Files

- `workers/{worker_name}/Dockerfile`: Docker image definition for the proposed worker.
- `workers/{worker_name}/app.py`: FastAPI worker with `/health` and `/run-task`.
- `workers/{worker_name}/requirements.txt`: Worker dependencies.
- `memory/prompts/{worker_name}.md`: Worker role, constraints, and future model notes.

## Proposed Modified Files

- `docker-compose.yml`: Add the proposed worker service on port `{port or "unassigned"}` after approval.
- `registry/workers.json`: Register `{worker_name}` with `model: none` for the first version after approval.
- `brain/worker_registry.py`: Add minimal routing for `{worker_type}` tasks after approval.
- `README.md`: Document startup and testing instructions after approval.

## Worker Draft

- worker_name: `{worker_name}`
- worker_type: `{worker_type}`
- port: `{port or "unassigned"}`
- model: `none`
- risk_level: `{risk_level}`

## Skills

{skills_text}

## Why This Shape

This proposal only describes a future worker. It does not create `workers/{worker_name}`, does not modify Docker Compose, and does not modify the worker registry. The worker should remain disposable and stateless, while the Brain remains responsible for memory loading, routing, approval, and task history.

## Risk Level

{risk_level}

The main risks are incorrect routing, port collision, and accidentally giving the worker access to long-term memory. The first implementation should use `model: none` and should only use `memory_context` passed by the Brain.

## Validation Plan

After approval and implementation:

1. Compile the worker Python file.
2. Validate `registry/workers.json`.
3. Validate Docker Compose config.
4. Build and start the worker.
5. Check `/health` on `127.0.0.1:{port or "PORT"}`.
6. Call `/run-task` with explicit `memory_context`.
7. Confirm the worker does not read `memory/`.
8. Confirm existing base-worker and doc-worker behavior is unchanged.

## Approval

This proposal is not approved yet.

No code should be modified, no `workers/{worker_name}` directory should be created, and no Docker Compose or registry changes should be made until the human explicitly approves this proposal.
"""
    path.write_text(content, encoding="utf-8")
    return path
