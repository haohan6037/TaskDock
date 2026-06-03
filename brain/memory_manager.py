from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_DIR = PROJECT_ROOT / "memory"
PROPOSALS_DIR = MEMORY_DIR / "proposals"

def read_text_if_exists(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def read_proposal_memory(proposal_id: str) -> str:
    normalized = proposal_id.zfill(3)
    matches = sorted(PROPOSALS_DIR.glob(f"{normalized}-*.md"))
    if not matches:
        return ""
    return matches[0].read_text(encoding="utf-8")

def retrieve_memory_context(task_text: str, proposal_id: Optional[str] = None) -> str:
    """
    Stage 1 memory retrieval:
    Keep it simple. Load only the core OpenClaw Brain memory.
    Later this can be replaced by keyword search, SQLite, or vector retrieval.
    """
    sections = []

    user_profile = read_text_if_exists(MEMORY_DIR / "user" / "profile.md")
    project_memory = read_text_if_exists(MEMORY_DIR / "projects" / "openclaw-brain.md")
    decision_memory = read_text_if_exists(MEMORY_DIR / "decisions" / "openclaw-brain-decisions.md")

    if user_profile:
        sections.append("## User Profile\n" + user_profile)
    if project_memory:
        sections.append("## Project Memory\n" + project_memory)
    if decision_memory:
        sections.append("## Decision Memory\n" + decision_memory)
    if proposal_id:
        proposal_memory = read_proposal_memory(proposal_id)
        if proposal_memory:
            sections.append(f"## Proposal {proposal_id.zfill(3)} Memory\n" + proposal_memory)

    return "\n\n".join(sections)
