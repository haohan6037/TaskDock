from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path("/Users/happyfamily/OpenClawBrain")
TEMPLATE_DIR = PROJECT_ROOT / "worker_templates" / "fastapi-basic"

REQUIRED_TEMPLATE_FILES = [
    "Dockerfile.template",
    "app.py.template",
    "requirements.txt",
    "prompt.md.template",
]


def validate_template_files() -> None:
    missing = [name for name in REQUIRED_TEMPLATE_FILES if not (TEMPLATE_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing worker template files: {', '.join(missing)}")


def load_template(name: str) -> str:
    validate_template_files()
    path = TEMPLATE_DIR / name
    if path.name not in REQUIRED_TEMPLATE_FILES:
        raise ValueError(f"Unsupported template file: {name}")
    return path.read_text(encoding="utf-8")


def render_template(name: str, values: dict[str, str]) -> str:
    content = load_template(name)
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", value)
    return content
