from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class IntentSignal:
    source: str
    account_name: str
    signal_type: str
    strength: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IntentSignalBatch:
    signals: list[IntentSignal] = field(default_factory=list)


class IntentSignals:
    @staticmethod
    def parse_csv(path: str | Path) -> IntentSignalBatch:
        records: list[IntentSignal] = []
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                records.append(
                    IntentSignal(
                        source=str(row.get("source", "csv")),
                        account_name=str(row.get("account_name", "")),
                        signal_type=str(row.get("signal_type", "unknown")),
                        strength=float(row.get("strength", 0) or 0),
                        metadata=row,
                    )
                )
        return IntentSignalBatch(signals=records)

    @staticmethod
    def from_rows(rows: Iterable[dict[str, Any]]) -> IntentSignalBatch:
        return IntentSignalBatch(
            signals=[
                IntentSignal(
                    source=str(row.get("source", "unknown")),
                    account_name=str(row.get("account_name", "")),
                    signal_type=str(row.get("signal_type", "unknown")),
                    strength=float(row.get("strength", 0) or 0),
                    metadata=dict(row),
                )
                for row in rows
            ]
        )
