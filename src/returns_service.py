from pathlib import Path

POLICY_PATH = Path("data/returns_policy.md")


def load_policy():
    return POLICY_PATH.read_text(encoding="utf-8")