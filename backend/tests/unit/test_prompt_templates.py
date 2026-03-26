from __future__ import annotations

from pathlib import Path


def test_prompt_templates_exist():
    prompt_dir = Path(__file__).resolve().parents[2] / "prompts"
    expected = {
        "icp_scoring.txt",
        "outbound_personalization.txt",
        "content_generation.txt",
        "deal_intelligence.txt",
        "retention_analysis.txt",
    }
    actual = {path.name for path in prompt_dir.iterdir() if path.is_file()}
    assert expected.issubset(actual)
