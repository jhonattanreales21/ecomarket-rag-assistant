from pathlib import Path

POLICY_PATH = Path("data/returns_policy.md")


def load_policy() -> str:
    """Read and return the full return policy document as a string."""
    return POLICY_PATH.read_text(encoding="utf-8")
