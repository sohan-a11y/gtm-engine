from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TranscriptInsight:
    summary: str
    action_items: list[str] = field(default_factory=list)
    competitor_mentions: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    metadata: dict[str, Any] = field(default_factory=dict)


class TranscriptParser:
    def parse(self, transcript_text: str) -> TranscriptInsight:
        summary = self._summarize(transcript_text)
        action_items = self._extract_action_items(transcript_text)
        competitor_mentions = self._extract_competitors(transcript_text)
        sentiment = "positive" if any(keyword in transcript_text.lower() for keyword in ["great", "excited", "yes"]) else "neutral"
        return TranscriptInsight(
            summary=summary,
            action_items=action_items,
            competitor_mentions=competitor_mentions,
            sentiment=sentiment,
            metadata={"word_count": len(transcript_text.split())},
        )

    def _summarize(self, transcript_text: str) -> str:
        cleaned = " ".join(transcript_text.split())
        return cleaned[:240] + ("..." if len(cleaned) > 240 else "")

    def _extract_action_items(self, transcript_text: str) -> list[str]:
        matches = re.findall(r"(?:action item|follow up|next step):\s*(.+?)(?:[.;\n]|$)", transcript_text, flags=re.IGNORECASE)
        return [match.strip() for match in matches]

    def _extract_competitors(self, transcript_text: str) -> list[str]:
        candidates = ["salesforce", "hubspot", "gong", "clay", "6sense", "apollo"]
        lowered = transcript_text.lower()
        return [candidate for candidate in candidates if candidate in lowered]
