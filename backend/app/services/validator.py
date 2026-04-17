"""XAF data integrity validation.

Compares declared control totals in the XAF (linesCount, totalDebit, totalCredit)
against computed values from the actual parsed data.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models.xaf_model import AuditFile


@dataclass
class ValidationCheck:
    """A single validation check result."""
    section: str          # "Opening Balance" or "Transactions"
    check: str            # e.g. "Line Count", "Total Debit"
    declared: str         # value from XAF header
    computed: str         # value computed from lines
    passed: bool          # whether they match


@dataclass
class ValidationResult:
    """Overall validation result."""
    checks: list[ValidationCheck]
    all_passed: bool
    summary: str  # e.g. "6/6 checks passed"


def _safe_decimal(value: str) -> Decimal:
    """Parse a string to Decimal, returning 0 on failure."""
    try:
        return Decimal(value) if value else Decimal("0")
    except InvalidOperation:
        return Decimal("0")


def _format_decimal(value: Decimal) -> str:
    """Format decimal to 2 decimal places with thousand separators."""
    return f"{value:,.2f}"


def validate_xaf(af: AuditFile) -> ValidationResult:
    """Run all validation checks against the parsed AuditFile."""
    checks: list[ValidationCheck] = []

    # Opening Balance validations
    ob = af.openingBalance
    if ob is not None:
        actual_count = len(ob.lines)
        declared_count = int(ob.linesCount) if ob.linesCount else 0

        sum_debit = sum(
            _safe_decimal(line.amnt)
            for line in ob.lines
            if line.amntTp == "D"
        )
        sum_credit = sum(
            _safe_decimal(line.amnt)
            for line in ob.lines
            if line.amntTp == "C"
        )
        declared_debit = _safe_decimal(ob.totalDebit)
        declared_credit = _safe_decimal(ob.totalCredit)

        checks.append(ValidationCheck(
            section="Opening Balance",
            check="Line Count",
            declared=str(declared_count),
            computed=str(actual_count),
            passed=declared_count == actual_count,
        ))
        checks.append(ValidationCheck(
            section="Opening Balance",
            check="Total Debit",
            declared=_format_decimal(declared_debit),
            computed=_format_decimal(sum_debit),
            passed=declared_debit == sum_debit,
        ))
        checks.append(ValidationCheck(
            section="Opening Balance",
            check="Total Credit",
            declared=_format_decimal(declared_credit),
            computed=_format_decimal(sum_credit),
            passed=declared_credit == sum_credit,
        ))
        checks.append(ValidationCheck(
            section="Opening Balance",
            check="Debit = Credit",
            declared=_format_decimal(declared_debit),
            computed=_format_decimal(declared_credit),
            passed=declared_debit == declared_credit,
        ))

    # Transaction validations
    txns = af.transactions
    if txns is not None:
        actual_count = 0
        sum_debit = Decimal("0")
        sum_credit = Decimal("0")

        for journal in txns.journals:
            for txn in journal.transactions:
                for line in txn.lines:
                    actual_count += 1
                    amnt = _safe_decimal(line.amnt)
                    if line.amntTp == "D":
                        sum_debit += amnt
                    elif line.amntTp == "C":
                        sum_credit += amnt

        declared_count = int(txns.linesCount) if txns.linesCount else 0
        declared_debit = _safe_decimal(txns.totalDebit)
        declared_credit = _safe_decimal(txns.totalCredit)

        checks.append(ValidationCheck(
            section="Transactions",
            check="Line Count",
            declared=str(declared_count),
            computed=str(actual_count),
            passed=declared_count == actual_count,
        ))
        checks.append(ValidationCheck(
            section="Transactions",
            check="Total Debit",
            declared=_format_decimal(declared_debit),
            computed=_format_decimal(sum_debit),
            passed=declared_debit == sum_debit,
        ))
        checks.append(ValidationCheck(
            section="Transactions",
            check="Total Credit",
            declared=_format_decimal(declared_credit),
            computed=_format_decimal(sum_credit),
            passed=declared_credit == sum_credit,
        ))
        checks.append(ValidationCheck(
            section="Transactions",
            check="Debit = Credit",
            declared=_format_decimal(declared_debit),
            computed=_format_decimal(declared_credit),
            passed=declared_debit == declared_credit,
        ))

    # P&L Net Result: sum all transactions on accounts with accTp = "P"
    if txns is not None and af.ledgerAccounts:
        pl_accounts = {la.accID for la in af.ledgerAccounts if la.accTp == "P"}

        if pl_accounts:
            pl_debit = Decimal("0")
            pl_credit = Decimal("0")

            for journal in txns.journals:
                for txn in journal.transactions:
                    for line in txn.lines:
                        if line.accID in pl_accounts:
                            amnt = _safe_decimal(line.amnt)
                            if line.amntTp == "D":
                                pl_debit += amnt
                            elif line.amntTp == "C":
                                pl_credit += amnt

            net_result = pl_credit - pl_debit

            checks.append(ValidationCheck(
                section="P&L Summary",
                check="Total Revenue (Credit)",
                declared="—",
                computed=_format_decimal(pl_credit),
                passed=True,
            ))
            checks.append(ValidationCheck(
                section="P&L Summary",
                check="Total Expenses (Debit)",
                declared="—",
                computed=_format_decimal(pl_debit),
                passed=True,
            ))
            checks.append(ValidationCheck(
                section="P&L Summary",
                check="Net Result",
                declared="Profit" if net_result >= 0 else "Loss",
                computed=_format_decimal(net_result),
                passed=True,
            ))

    passed_count = sum(1 for c in checks if c.passed)
    total_count = len(checks)
    all_passed = passed_count == total_count

    return ValidationResult(
        checks=checks,
        all_passed=all_passed,
        summary=f"{passed_count}/{total_count} checks passed",
    )
