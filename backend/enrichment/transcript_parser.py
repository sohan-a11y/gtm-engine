import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TranscriptInsight:
    summary: str
    action_items: list[str] = field(default_factory=list)
    competitor_mentions: list[str] = field(default_factory=list)
    buying_signals: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    engagement_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Minimal mock router used when no real router is injected
# ---------------------------------------------------------------------------


class _MockLLMRouter:
    """Deterministic fallback used in tests / when no LLM is configured."""

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        format: Optional[str] = None,
    ) -> str:
        payload: dict[str, Any] = {
            "summary": "Meeting discussed product requirements and next steps.",
            "action_items": ["Send follow-up email", "Schedule demo"],
            "competitor_mentions": [],
            "buying_signals": ["expressed interest in pricing"],
            "objections": [],
            "sentiment": "positive",
            "engagement_score": 0.72,
        }
        return json.dumps(payload)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a sales intelligence analyst. Extract structured insights from the sales call transcript provided.

Return ONLY valid JSON with these exact keys:
- summary: string (3-5 sentences summarising the call)
- action_items: array of strings (concrete next steps mentioned)
- competitor_mentions: array of strings (competitor names mentioned)
- buying_signals: array of strings (positive buying intent phrases)
- objections: array of strings (pushbacks or concerns raised)
- sentiment: one of "positive", "neutral", "negative", "mixed"
- engagement_score: float between 0.0 and 1.0 (0=disengaged, 1=highly engaged)

Do not include any text outside the JSON object."""

_KNOWN_COMPETITORS = [
    "salesforce",
    "hubspot",
    "gong",
    "clay",
    "6sense",
    "apollo",
    "outreach",
    "salesloft",
    "clearbit",
    "zoominfo",
]


class TranscriptParser:
    """LLM-powered transcript parser with regex fallback."""

    def __init__(self, llm_router: Any = None) -> None:
        self._llm = llm_router or _MockLLMRouter()

    # ------------------------------------------------------------------
    # Public entry-points
    # ------------------------------------------------------------------

    def parse(self, transcript_text: str) -> TranscriptInsight:
        """Parse a plain-text transcript and return structured insights."""
        try:
            return self._parse_with_llm(transcript_text)
        except Exception as exc:
            logger.warning("LLM transcript parse failed, falling back to regex: %s", exc)
            return self._parse_with_regex(transcript_text)

    # ------------------------------------------------------------------
    # Format converters
    # ------------------------------------------------------------------

    @classmethod
    def from_zoom_vtt(cls, vtt_text: str) -> str:
        """Strip Zoom VTT timestamps and return plain transcript text."""
        # Remove WEBVTT header line
        lines = vtt_text.splitlines()
        text_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "WEBVTT":
                continue
            # Skip timestamp lines like "00:00:01.000 --> 00:00:04.000"
            if re.match(r"^\d{2}:\d{2}:\d{2}[\.,]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[\.,]\d{3}", stripped):
                continue
            # Skip cue identifier lines (pure digits or digits with dots)
            if re.match(r"^\d+$", stripped):
                continue
            text_lines.append(stripped)
        return " ".join(text_lines)

    @classmethod
    def from_gong_json(cls, payload: dict[str, Any]) -> str:
        """Extract plain text from a Gong webhook JSON payload.

        Gong structure: payload.transcript.utterances[].words[].text
        """
        try:
            transcript = payload.get("payload", payload).get("transcript", {})
            utterances = transcript.get("utterances", [])
            parts: list[str] = []
            for utterance in utterances:
                words = utterance.get("words", [])
                sentence = " ".join(w.get("text", "") for w in words if w.get("text"))
                if sentence:
                    parts.append(sentence)
            return " ".join(parts)
        except Exception as exc:
            logger.warning("from_gong_json extraction failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_with_llm(self, transcript_text: str) -> TranscriptInsight:
        # Truncate very long transcripts to ~8000 chars to stay within context
        _max_chars: int = 8000
        user_prompt = transcript_text[:_max_chars]

        raw: Any = self._llm.complete(
            user_prompt,
            system_prompt=_SYSTEM_PROMPT,
            format="json",
        )
        # Handle awaitable (real LLMRouter returns a coroutine)
        import inspect

        if inspect.isawaitable(raw):
            import asyncio

            raw = asyncio.get_event_loop().run_until_complete(raw)

        # The real LLMRouter wraps the response in an LLMResponse dataclass
        if hasattr(raw, "content"):
            raw = raw.content  # type: ignore[union-attr]

        raw_str: str = raw if isinstance(raw, str) else json.dumps(raw)
        # Strip markdown fences if present
        raw_str = raw_str.strip()
        if raw_str.startswith("```"):
            raw_str = re.sub(r"^```(?:json)?\s*", "", raw_str)
            raw_str = re.sub(r"\s*```$", "", raw_str)

        data: dict[str, Any] = json.loads(raw_str.strip())

        return TranscriptInsight(
            summary=str(data.get("summary", "")),
            action_items=list(data.get("action_items", [])),
            competitor_mentions=list(data.get("competitor_mentions", [])),
            buying_signals=list(data.get("buying_signals", [])),
            objections=list(data.get("objections", [])),
            sentiment=str(data.get("sentiment", "neutral")),
            engagement_score=float(data.get("engagement_score", 0.5)),
            metadata={"word_count": len(transcript_text.split()), "source": "llm"},
        )

    def _parse_with_regex(self, transcript_text: str) -> TranscriptInsight:
        cleaned = " ".join(transcript_text.split())
        summary = cleaned[:480] + ("..." if len(cleaned) > 480 else "")
        action_items = re.findall(
            r"(?:action item|follow up|next step):\s*(.+?)(?:[.;\n]|$)",
            transcript_text,
            flags=re.IGNORECASE,
        )
        lowered = transcript_text.lower()
        competitor_mentions = [c for c in _KNOWN_COMPETITORS if c in lowered]

        buying_signals: list[str] = []
        for pattern in [r"(?:very interested|ready to buy|let's move forward|send.*contract|pricing.*question)", r"(?:when can we start|budget approved)"]:
            for match in re.finditer(pattern, transcript_text, flags=re.IGNORECASE):
                buying_signals.append(match.group(0))

        objections: list[str] = []
        for pattern in [r"(?:too expensive|not sure|need to think|talk to.*team|concern about)"]:
            for match in re.finditer(pattern, transcript_text, flags=re.IGNORECASE):
                objections.append(match.group(0))

        positive_words = {"great", "excited", "yes", "perfect", "love", "amazing"}
        negative_words = {"no", "concerned", "expensive", "not sure", "problem"}
        pos_count = sum(1 for w in positive_words if w in lowered)
        neg_count = sum(1 for w in negative_words if w in lowered)
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        word_count = len(transcript_text.split())
        raw_score: float = word_count / 1000.0
        engagement_score: float = min(1.0, int(raw_score * 100) / 100.0)

        return TranscriptInsight(
            summary=summary,
            action_items=[m.strip() for m in action_items],
            competitor_mentions=competitor_mentions,
            buying_signals=buying_signals,
            objections=objections,
            sentiment=sentiment,
            engagement_score=engagement_score,
            metadata={"word_count": word_count, "source": "regex"},
        )
