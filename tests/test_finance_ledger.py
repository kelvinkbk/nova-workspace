from decimal import Decimal

import pytest

from core.runtime import RuntimeState
from finance.ledger import FinanceLedger
from security.policy import SecurityPolicy


def test_empty_ledger_reports_no_verified_revenue(tmp_path):
    ledger = FinanceLedger(tmp_path / "finance.sqlite3")

    summary = ledger.summary()
    status = ledger.format_status()

    assert summary["verified_income_paise"] == 0
    assert summary["net_earned_paise"] == 0
    assert "no verified revenue recorded yet" in status
    assert "₹0.00 / ₹100.00" in status


def test_pending_income_does_not_count_as_revenue(tmp_path):
    ledger = FinanceLedger(tmp_path / "finance.sqlite3")
    ledger.record_transaction(
        kind="income", amount="100", description="Awaiting payment confirmation"
    )

    summary = ledger.summary()

    assert summary["verified_income_paise"] == 0
    assert summary["pending_count"] == 1


def test_verified_income_requires_evidence_reference(tmp_path):
    ledger = FinanceLedger(tmp_path / "finance.sqlite3")

    with pytest.raises(ValueError, match="evidence reference"):
        ledger.record_transaction(
            kind="income", amount=100, description="Customer payment", verified=True
        )


def test_verified_income_and_expenses_are_separated_from_owner_funding(tmp_path):
    ledger = FinanceLedger(tmp_path / "finance.sqlite3")
    ledger.record_transaction(
        kind="income", amount=Decimal("125.50"), description="Paid order",
        evidence_ref="receipt-001", verified=True,
    )
    ledger.record_transaction(
        kind="expense", amount="25.25", description="Service expense",
        evidence_ref="receipt-002", verified=True,
    )
    ledger.record_transaction(
        kind="owner_funding", amount="500", description="Owner contribution",
        evidence_ref="bank-ref-003", verified=True,
    )

    summary = ledger.summary()

    assert summary["verified_income_paise"] == 12_550
    assert summary["verified_expense_paise"] == 2_525
    assert summary["verified_owner_funding_paise"] == 50_000
    assert summary["net_earned_paise"] == 10_025
    assert summary["target_progress_paise"] == 10_000


def test_rejects_invalid_money_and_unknown_transaction_kinds(tmp_path):
    ledger = FinanceLedger(tmp_path / "finance.sqlite3")

    with pytest.raises(ValueError):
        ledger.record_transaction(kind="income", amount="NaN", description="Bad amount")
    with pytest.raises(ValueError):
        ledger.record_transaction(kind="income", amount=0, description="Zero amount")
    with pytest.raises(ValueError):
        ledger.record_transaction(kind="transfer", amount=10, description="Unsupported")
    with pytest.raises(ValueError):
        ledger.record_transaction(kind="income", amount="1e999", description="Too large")


def test_runtime_exposes_finance_summary_as_read_only_action():
    runtime = RuntimeState()

    assert runtime.registry.get("finance_status") is not None
    assert SecurityPolicy().evaluate("finance_status").allowed is True
    status = runtime.registry.get("finance_status").handler()
    assert "Verified revenue:" in status
    assert "Owner funding is tracked separately" in status
