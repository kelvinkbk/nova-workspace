"""Evidence-based finance ledger for NOVA.

This module deliberately records financial events only when explicitly called by
trusted application code. The autonomous agent gets read-only summary access.
No payment provider or bank integration is performed here.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "ledger.sqlite3"
_ALLOWED_KINDS = {"income", "expense", "owner_funding"}


class FinanceLedger:
    """Small local ledger that separates earned revenue from owner funding."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_LEDGER_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL CHECK(kind IN ('income', 'expense', 'owner_funding')),
                    amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
                    description TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK(status IN ('pending', 'verified')),
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _amount_to_paise(amount: Decimal | int | float | str) -> int:
        if isinstance(amount, bool):
            raise ValueError("Amount must be a positive monetary value.")
        try:
            parsed = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Amount must be a valid monetary value.") from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ValueError("Amount must be finite and greater than zero.")
        try:
            rounded = parsed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError("Amount is too large to record safely.") from exc
        paise = int(rounded * 100)
        if paise <= 0:
            raise ValueError("Amount must be at least ₹0.01.")
        return paise

    def record_transaction(
        self,
        *,
        kind: str,
        amount: Decimal | int | float | str,
        description: str,
        evidence_ref: str = "",
        verified: bool = False,
    ) -> int:
        """Record a ledger item; verified entries require an evidence reference.

        This is intentionally not exposed as an autonomous runtime action. A
        caller must be trusted to mark an event verified only after checking it.
        """
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"kind must be one of: {', '.join(sorted(_ALLOWED_KINDS))}.")
        clean_description = description.strip() if isinstance(description, str) else ""
        if not clean_description:
            raise ValueError("A non-empty description is required.")
        clean_evidence = evidence_ref.strip() if isinstance(evidence_ref, str) else ""
        if not isinstance(verified, bool):
            raise ValueError("verified must be a boolean.")
        if verified and not clean_evidence:
            raise ValueError("Verified transactions require an evidence reference.")
        amount_paise = self._amount_to_paise(amount)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO finance_transactions
                    (kind, amount_paise, description, evidence_ref, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    kind,
                    amount_paise,
                    clean_description,
                    clean_evidence,
                    "verified" if verified else "pending",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def summary(self) -> dict[str, int]:
        """Return totals in paise; pending items never count as actual money."""
        totals = {
            "verified_income_paise": 0,
            "verified_expense_paise": 0,
            "verified_owner_funding_paise": 0,
            "pending_count": 0,
            "verified_count": 0,
        }
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT kind, status, COALESCE(SUM(amount_paise), 0) AS total, COUNT(*) AS count
                FROM finance_transactions
                GROUP BY kind, status
                """
            ).fetchall()
        for row in rows:
            if row["status"] == "pending":
                totals["pending_count"] += int(row["count"])
                continue
            totals["verified_count"] += int(row["count"])
            key = {
                "income": "verified_income_paise",
                "expense": "verified_expense_paise",
                "owner_funding": "verified_owner_funding_paise",
            }[row["kind"]]
            totals[key] += int(row["total"])
        totals["net_earned_paise"] = (
            totals["verified_income_paise"] - totals["verified_expense_paise"]
        )
        totals["target_progress_paise"] = max(0, min(10_000, totals["verified_income_paise"]))
        return totals

    def format_status(self) -> str:
        totals = self.summary()
        income = totals["verified_income_paise"] / 100
        expenses = totals["verified_expense_paise"] / 100
        net = totals["net_earned_paise"] / 100
        funding = totals["verified_owner_funding_paise"] / 100
        progress = totals["target_progress_paise"] / 100
        lines = [
            "NOVA FINANCE STATUS (evidence-based)",
            f"Verified revenue: ₹{income:.2f}",
            f"Verified expenses: ₹{expenses:.2f}",
            f"Net earned (excluding owner funding): ₹{net:.2f}",
            f"Verified owner funding: ₹{funding:.2f}",
            f"First ₹100 revenue target: ₹{progress:.2f} / ₹100.00",
            f"Pending entries excluded from totals: {totals['pending_count']}",
            "Revenue status: " + ("verified revenue recorded" if income > 0 else "no verified revenue recorded yet"),
            "Owner funding is tracked separately and never counted as earned revenue.",
        ]
        return "\n".join(lines)


def finance_status() -> str:
    """Read-only runtime tool for the autonomous agent."""
    return FinanceLedger().format_status()
