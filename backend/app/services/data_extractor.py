"""Extract flattened tabular data from parsed AuditFile for export/preview.

Each data type produces a list of flat dicts suitable for CSV/XLSX/JSON/Parquet export.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from ..models.xaf_model import AuditFile


# Mapping of data type keys to display names
DATA_TYPE_DISPLAY = {
    "header": "Header",
    "company": "Company",
    "customers_suppliers": "Customers & Suppliers",
    "ledger_accounts": "General Ledger",
    "vat_codes": "VAT Codes",
    "periods": "Periods",
    "opening_balance": "Opening Balance",
    "transactions": "Transaction Lines",
}

# Ordered list of data types
DATA_TYPE_KEYS = list(DATA_TYPE_DISPLAY.keys())


def extract_all(af: AuditFile) -> dict[str, list[dict[str, Any]]]:
    """Extract all data types from an AuditFile into flat dicts.

    Returns a dict mapping data type key to list of row dicts.
    """
    result = {}
    for key in DATA_TYPE_KEYS:
        rows = extract_data_type(af, key)
        if rows:
            result[key] = rows
    return result


def get_record_counts(parsed_data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """Get record counts for each available data type."""
    return {key: len(rows) for key, rows in parsed_data.items()}


def extract_data_type(af: AuditFile, data_type: str) -> list[dict[str, Any]]:
    """Extract a single data type from the AuditFile."""
    extractors = {
        "header": _extract_header,
        "company": _extract_company,
        "customers_suppliers": _extract_customers_suppliers,
        "ledger_accounts": _extract_ledger_accounts,
        "vat_codes": _extract_vat_codes,
        "periods": _extract_periods,
        "opening_balance": _extract_opening_balance,
        "transactions": _extract_transactions,
    }
    extractor = extractors.get(data_type)
    if extractor is None:
        return []
    return extractor(af)


def _extract_header(af: AuditFile) -> list[dict[str, Any]]:
    """Extract header as a single-row table."""
    h = af.header
    row = {
        "fiscalYear": h.fiscalYear,
        "startDate": h.startDate,
        "endDate": h.endDate,
        "curCode": h.curCode,
        "dateCreated": h.dateCreated,
        "softwareDesc": h.softwareDesc,
        "softwareVersion": h.softwareVersion,
        "xafVersion": af.sourceVersion,
    }
    if h.rgsVersion:
        row["rgsVersion"] = h.rgsVersion
    if h.auditfileVersion:
        row["auditfileVersion"] = h.auditfileVersion
    if h.softwareID:
        row["softwareID"] = h.softwareID
    return [row]


def _extract_company(af: AuditFile) -> list[dict[str, Any]]:
    """Extract company info as a single-row table, with addresses flattened."""
    c = af.company
    row: dict[str, Any] = {
        "companyName": c.companyName,
        "taxRegistrationCountry": c.taxRegistrationCountry,
        "taxRegIdent": c.taxRegIdent,
    }
    if c.companyIdent:
        row["companyIdent"] = c.companyIdent
    if c.commerceNr:
        row["commerceNr"] = c.commerceNr

    # Flatten first street address
    if c.streetAddresses:
        addr = c.streetAddresses[0]
        for field_name in ("streetname", "number", "numberExtension", "city", "postalCode", "country"):
            val = getattr(addr, field_name, None)
            if val:
                row[f"street_{field_name}"] = val

    return [row]


def _extract_customers_suppliers(af: AuditFile) -> list[dict[str, Any]]:
    """Extract customers/suppliers as a flat table."""
    rows = []
    for cs in af.customersSuppliers:
        row: dict[str, Any] = {
            "custSupID": cs.custSupID,
            "custSupName": cs.custSupName or "",
            "eMail": cs.eMail or "",
            "commerceNr": cs.commerceNr or "",
            "taxRegistrationCountry": cs.taxRegistrationCountry or "",
            "taxRegIdent": cs.taxRegIdent or "",
            "custSupTp": cs.custSupTp or "",
            "opBalDesc": cs.opBalDesc or "",
            "opBalTp": cs.opBalTp or "",
            "clBalDesc": cs.clBalDesc or "",
            "clBalTp": cs.clBalTp or "",
        }
        # Add 3.x-only fields if present
        if cs.contact:
            row["contact"] = cs.contact
        if cs.telephone:
            row["telephone"] = cs.telephone
        if cs.fax:
            row["fax"] = cs.fax
        if cs.website:
            row["website"] = cs.website

        # Flatten first street address
        if cs.streetAddresses:
            addr = cs.streetAddresses[0]
            for fn in ("streetname", "number", "numberExtension", "city", "postalCode", "country"):
                val = getattr(addr, fn, None)
                if val:
                    row[f"street_{fn}"] = val

        rows.append(row)
    return rows


def _extract_ledger_accounts(af: AuditFile) -> list[dict[str, Any]]:
    """Extract ledger accounts as a flat table."""
    rows = []
    for la in af.ledgerAccounts:
        row: dict[str, Any] = {
            "accID": la.accID,
            "accDesc": la.accDesc,
            "accTp": la.accTp,
        }
        if la.rgsCode:
            row["rgsCode"] = la.rgsCode
        if la.leadCode:
            row["leadCode"] = la.leadCode
        if la.leadDescription:
            row["leadDescription"] = la.leadDescription
        rows.append(row)
    return rows


def _extract_vat_codes(af: AuditFile) -> list[dict[str, Any]]:
    """Extract VAT codes as a flat table."""
    return [
        {
            "vatID": vc.vatID,
            "vatDesc": vc.vatDesc,
            "vatToPayAccID": vc.vatToPayAccID or "",
            "vatToClaimAccID": vc.vatToClaimAccID or "",
        }
        for vc in af.vatCodes
    ]


def _extract_periods(af: AuditFile) -> list[dict[str, Any]]:
    """Extract periods as a flat table."""
    rows = []
    for p in af.periods:
        row: dict[str, Any] = {
            "periodNumber": p.periodNumber,
            "startDatePeriod": p.startDatePeriod,
            "endDatePeriod": p.endDatePeriod,
        }
        if p.periodDesc:
            row["periodDesc"] = p.periodDesc
        rows.append(row)
    return rows


def _extract_opening_balance(af: AuditFile) -> list[dict[str, Any]]:
    """Extract opening balance lines as a flat table."""
    ob = af.openingBalance
    if ob is None:
        return []
    return [
        {
            "nr": line.nr,
            "accID": line.accID,
            "amnt": line.amnt,
            "amntTp": line.amntTp,
        }
        for line in ob.lines
    ]


def _extract_transactions(af: AuditFile) -> list[dict[str, Any]]:
    """Extract transaction lines as a flat table (denormalized with journal/transaction info)."""
    txns = af.transactions
    if txns is None:
        return []

    rows = []
    for journal in txns.journals:
        for txn in journal.transactions:
            for line in txn.lines:
                row: dict[str, Any] = {
                    "jrnID": journal.jrnID,
                    "jrnDesc": journal.desc,
                    "jrnTp": journal.jrnTp or "",
                    "txnNr": txn.nr,
                    "txnDesc": txn.desc or "",
                    "periodNumber": txn.periodNumber,
                    "trDt": txn.trDt,
                    "source": txn.source or "",
                    "user": txn.user or "",
                    "lineNr": line.nr,
                    "accID": line.accID,
                    "docRef": line.docRef,
                    "effDate": line.effDate,
                    "desc": line.desc or "",
                    "amnt": line.amnt,
                    "amntTp": line.amntTp,
                    "custSupID": line.custSupID or "",
                    "invRef": line.invRef or "",
                }
                # Optional fields
                if line.settDate:
                    row["settDate"] = line.settDate
                if line.receivingDocRef:
                    row["receivingDocRef"] = line.receivingDocRef
                if line.shipDocRef:
                    row["shipDocRef"] = line.shipDocRef
                if line.cost:
                    row["cost"] = line.cost
                if line.product:
                    row["product"] = line.product
                if line.project:
                    row["project"] = line.project
                if line.workCostArrRef:
                    row["workCostArrRef"] = line.workCostArrRef
                if line.bankAccNr:
                    row["bankAccNr"] = line.bankAccNr
                if line.offsetBankAccNr:
                    row["offsetBankAccNr"] = line.offsetBankAccNr

                # VAT entries (flatten first VAT if present)
                if line.vat:
                    v = line.vat[0]
                    row["vatID"] = v.vatID
                    row["vatPerc"] = v.vatPerc
                    row["vatAmnt"] = v.vatAmnt
                    row["vatAmntTp"] = v.vatAmntTp

                # Currency
                if line.currency:
                    row["curCode"] = line.currency.curCode
                    row["curAmnt"] = line.currency.curAmnt

                rows.append(row)
    return rows
