"""Streaming XML parser for XAF 3.1, 3.2, and 4.0 files.

Uses defusedxml for initial validation and lxml.etree.iterparse for
streaming to handle large files efficiently.
"""

from __future__ import annotations

import io
from typing import Callable, Optional

import defusedxml.ElementTree as DefusedET
from lxml import etree

from ..models.xaf_model import (
    Address,
    AuditFile,
    BankAccount,
    Company,
    CurrencyEntry,
    CustomerSupplier,
    Header,
    Journal,
    LedgerAccount,
    OpeningBalance,
    OpeningBalanceLine,
    Period,
    Transaction,
    TransactionLine,
    Transactions,
    VatCode,
    VatEntry,
)
from ..utils.security import sanitize_string


# Namespace URI to version mapping
NAMESPACE_MAP = {
    "http://www.auditfiles.nl/XAF/3.1": "3.1",
    "http://www.auditfiles.nl/XAF/3.2": "3.2",
    "http://www.odb.belastingdienst.nl/Belastingdienst/BCPP/1.1/structures/XmlauditfileXAF_4.0": "4.0",
}


class XAFParseError(Exception):
    """Raised when the XAF file cannot be parsed."""
    pass


def _safe_text(element: Optional[etree._Element]) -> Optional[str]:
    """Extract text from an element, sanitizing it."""
    if element is None:
        return None
    text = element.text
    if text is None:
        return None
    return sanitize_string(text.strip())


def _get_child_text(parent: etree._Element, tag: str, ns: str) -> Optional[str]:
    """Get text of a direct child element by local name."""
    child = parent.find(f"{{{ns}}}{tag}")
    return _safe_text(child)


def detect_version(content: bytes) -> tuple[str, str]:
    """Detect XAF version from namespace URI.

    Returns (version, namespace_uri).
    Raises XAFParseError if version cannot be detected.
    """
    # Use defusedxml for safe initial parsing
    try:
        tree = DefusedET.fromstring(content)
    except Exception as exc:
        raise XAFParseError(f"Invalid XML: {exc}") from exc

    # The root tag includes the namespace: {namespace}auditfile
    root_tag = tree.tag
    if "}" in root_tag:
        ns = root_tag.split("}")[0].lstrip("{")
    else:
        raise XAFParseError("No namespace found on root element. Cannot determine XAF version.")

    version = NAMESPACE_MAP.get(ns)
    if version is None:
        raise XAFParseError(f"Unknown XAF namespace: {ns}")

    return version, ns


def parse_xaf(
    content: bytes,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> AuditFile:
    """Parse an XAF file and return a normalized AuditFile.

    Args:
        content: Raw bytes of the XAF file.
        progress_callback: Optional callback(percentage, message) for progress updates.

    Returns:
        Populated AuditFile dataclass.

    Raises:
        XAFParseError: If the file cannot be parsed.
    """
    if progress_callback:
        progress_callback(0, "Detecting XAF version...")

    version, ns = detect_version(content)

    if progress_callback:
        progress_callback(5, f"Detected XAF version {version}")

    audit_file = AuditFile(sourceVersion=version, sourceNamespace=ns)

    # Create a safe lxml parser
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        dtd_validation=False,
        load_dtd=False,
        huge_tree=False,
    )

    try:
        tree = etree.parse(io.BytesIO(content), parser)
    except etree.XMLSyntaxError as exc:
        raise XAFParseError(f"XML syntax error: {exc}") from exc

    root = tree.getroot()

    # Parse sections with progress
    if progress_callback:
        progress_callback(10, "Parsing header...")
    _parse_header(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(20, "Parsing company info...")
    _parse_company(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(30, "Parsing customers/suppliers...")
    _parse_customers_suppliers(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(45, "Parsing general ledger...")
    _parse_general_ledger(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(55, "Parsing VAT codes...")
    _parse_vat_codes(root, ns, audit_file)

    if progress_callback:
        progress_callback(60, "Parsing periods...")
    _parse_periods(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(65, "Parsing opening balance...")
    _parse_opening_balance(root, ns, version, audit_file)

    if progress_callback:
        progress_callback(70, "Parsing transactions...")
    _parse_transactions(root, ns, version, audit_file, progress_callback)

    if progress_callback:
        progress_callback(100, "Parsing complete")

    return audit_file


def _parse_header(root: etree._Element, ns: str, version: str, af: AuditFile) -> None:
    """Parse the header section."""
    header_el = root.find(f"{{{ns}}}header")
    if header_el is None:
        raise XAFParseError("Missing required <header> element")

    h = af.header
    h.fiscalYear = _get_child_text(header_el, "fiscalYear", ns) or ""
    h.startDate = _get_child_text(header_el, "startDate", ns) or ""
    h.endDate = _get_child_text(header_el, "endDate", ns) or ""
    h.curCode = _get_child_text(header_el, "curCode", ns) or ""
    h.dateCreated = _get_child_text(header_el, "dateCreated", ns) or ""
    h.softwareDesc = _get_child_text(header_el, "softwareDesc", ns) or ""
    h.softwareVersion = _get_child_text(header_el, "softwareVersion", ns) or ""

    if version == "4.0":
        h.rgsVersion = _get_child_text(header_el, "RGSVersion", ns)
    else:
        h.auditfileVersion = _get_child_text(header_el, "auditfileVersion", ns)
        h.softwareID = _get_child_text(header_el, "softwareID", ns)


def _parse_address(addr_el: etree._Element, ns: str) -> Address:
    """Parse an address element (streetAddress or postalAddress)."""
    return Address(
        streetname=_get_child_text(addr_el, "streetname", ns),
        number=_get_child_text(addr_el, "number", ns),
        numberExtension=_get_child_text(addr_el, "numberExtension", ns),
        property=_get_child_text(addr_el, "property", ns),
        city=_get_child_text(addr_el, "city", ns),
        postalCode=_get_child_text(addr_el, "postalCode", ns),
        region=_get_child_text(addr_el, "region", ns),
        country=_get_child_text(addr_el, "country", ns),
    )


def _parse_company(root: etree._Element, ns: str, version: str, af: AuditFile) -> None:
    """Parse the company section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        raise XAFParseError("Missing required <company> element")

    c = af.company
    if version == "4.0":
        c.commerceNr = _get_child_text(company_el, "Commercenr", ns)
    else:
        c.companyIdent = _get_child_text(company_el, "companyIdent", ns)

    c.companyName = _get_child_text(company_el, "companyName", ns) or ""
    c.taxRegistrationCountry = _get_child_text(company_el, "taxRegistrationCountry", ns) or ""
    c.taxRegIdent = _get_child_text(company_el, "taxRegIdent", ns) or ""

    # Street addresses
    for addr_el in company_el.findall(f"{{{ns}}}streetAddress"):
        c.streetAddresses.append(_parse_address(addr_el, ns))

    # Postal addresses (3.x only)
    if version != "4.0":
        for addr_el in company_el.findall(f"{{{ns}}}postalAddress"):
            c.postalAddresses.append(_parse_address(addr_el, ns))


def _parse_customers_suppliers(
    root: etree._Element, ns: str, version: str, af: AuditFile
) -> None:
    """Parse the customersSuppliers section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    cs_el = company_el.find(f"{{{ns}}}customersSuppliers")
    if cs_el is None:
        return

    for cs_item in cs_el.findall(f"{{{ns}}}customerSupplier"):
        cs = CustomerSupplier(
            custSupID=_get_child_text(cs_item, "custSupID", ns) or "",
            custSupName=_get_child_text(cs_item, "custSupName", ns),
            eMail=_get_child_text(cs_item, "eMail", ns),
            commerceNr=_get_child_text(cs_item, "commerceNr", ns),
            taxRegistrationCountry=_get_child_text(cs_item, "taxRegistrationCountry", ns),
            taxRegIdent=_get_child_text(cs_item, "taxRegIdent", ns),
            custSupTp=_get_child_text(cs_item, "custSupTp", ns),
            opBalDesc=_get_child_text(cs_item, "opBalDesc", ns),
            opBalTp=_get_child_text(cs_item, "opBalTp", ns),
            clBalDesc=_get_child_text(cs_item, "clBalDesc", ns),
            clBalTp=_get_child_text(cs_item, "clBalTp", ns),
        )

        # Version-specific fields
        if version != "4.0":
            cs.contact = _get_child_text(cs_item, "contact", ns)
            cs.telephone = _get_child_text(cs_item, "telephone", ns)
            cs.fax = _get_child_text(cs_item, "fax", ns)
            cs.website = _get_child_text(cs_item, "website", ns)
            cs.relationshipID = _get_child_text(cs_item, "relationshipID", ns)
            cs.custSupGrpID = _get_child_text(cs_item, "custSupGrpID", ns)
            cs.custCreditLimit = _get_child_text(cs_item, "custCreditLimit", ns)
            cs.supplierLimit = _get_child_text(cs_item, "supplierLimit", ns)

            # Bank accounts (3.x only)
            for ba_el in cs_item.findall(f"{{{ns}}}bankAccount"):
                ba = BankAccount(
                    bankAccNr=_get_child_text(ba_el, "bankAccNr", ns) or "",
                    bankIdCd=_get_child_text(ba_el, "bankIdCd", ns),
                )
                cs.bankAccounts.append(ba)

            # Postal addresses (3.x only)
            for addr_el in cs_item.findall(f"{{{ns}}}postalAddress"):
                cs.postalAddresses.append(_parse_address(addr_el, ns))

        # Street addresses (all versions)
        for addr_el in cs_item.findall(f"{{{ns}}}streetAddress"):
            cs.streetAddresses.append(_parse_address(addr_el, ns))

        af.customersSuppliers.append(cs)


def _parse_general_ledger(
    root: etree._Element, ns: str, version: str, af: AuditFile
) -> None:
    """Parse the generalLedger section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    gl_el = company_el.find(f"{{{ns}}}generalLedger")
    if gl_el is None:
        return

    for la_el in gl_el.findall(f"{{{ns}}}ledgerAccount"):
        la = LedgerAccount(
            accID=_get_child_text(la_el, "accID", ns) or "",
            accDesc=_get_child_text(la_el, "accDesc", ns) or "",
            accTp=_get_child_text(la_el, "accTp", ns) or "",
        )

        if version == "4.0":
            la.rgsCode = _get_child_text(la_el, "RGScode", ns)
        else:
            la.leadCode = _get_child_text(la_el, "leadCode", ns)
            la.leadDescription = _get_child_text(la_el, "leadDescription", ns)
            la.leadReference = _get_child_text(la_el, "leadReference", ns)
            la.leadCrossRef = _get_child_text(la_el, "leadCrossRef", ns)

        af.ledgerAccounts.append(la)


def _parse_vat_codes(root: etree._Element, ns: str, af: AuditFile) -> None:
    """Parse the vatCodes section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    vc_el = company_el.find(f"{{{ns}}}vatCodes")
    if vc_el is None:
        return

    for vc_item in vc_el.findall(f"{{{ns}}}vatCode"):
        af.vatCodes.append(VatCode(
            vatID=_get_child_text(vc_item, "vatID", ns) or "",
            vatDesc=_get_child_text(vc_item, "vatDesc", ns) or "",
            vatToPayAccID=_get_child_text(vc_item, "vatToPayAccID", ns),
            vatToClaimAccID=_get_child_text(vc_item, "vatToClaimAccID", ns),
        ))


def _parse_periods(root: etree._Element, ns: str, version: str, af: AuditFile) -> None:
    """Parse the periods section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    periods_el = company_el.find(f"{{{ns}}}periods")
    if periods_el is None:
        return

    for p_el in periods_el.findall(f"{{{ns}}}period"):
        p = Period(
            periodNumber=_get_child_text(p_el, "periodNumber", ns) or "",
            startDatePeriod=_get_child_text(p_el, "startDatePeriod", ns) or "",
            endDatePeriod=_get_child_text(p_el, "endDatePeriod", ns) or "",
        )
        if version != "4.0":
            p.periodDesc = _get_child_text(p_el, "periodDesc", ns)
            p.startTimePeriod = _get_child_text(p_el, "startTimePeriod", ns)
            p.endTimePeriod = _get_child_text(p_el, "endTimePeriod", ns)

        af.periods.append(p)


def _parse_opening_balance(
    root: etree._Element, ns: str, version: str, af: AuditFile
) -> None:
    """Parse the openingBalance section."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    ob_el = company_el.find(f"{{{ns}}}openingBalance")
    if ob_el is None:
        return

    ob = OpeningBalance(
        linesCount=_get_child_text(ob_el, "linesCount", ns) or "",
        totalDebit=_get_child_text(ob_el, "totalDebit", ns) or "",
        totalCredit=_get_child_text(ob_el, "totalCredit", ns) or "",
    )

    if version != "4.0":
        ob.opBalDate = _get_child_text(ob_el, "opBalDate", ns)
        ob.opBalDesc = _get_child_text(ob_el, "opBalDesc", ns)

    for line_el in ob_el.findall(f"{{{ns}}}obLine"):
        ob.lines.append(OpeningBalanceLine(
            nr=_get_child_text(line_el, "nr", ns) or "",
            accID=_get_child_text(line_el, "accID", ns) or "",
            amnt=_get_child_text(line_el, "amnt", ns) or "",
            amntTp=_get_child_text(line_el, "amntTp", ns) or "",
        ))

    af.openingBalance = ob


def _parse_transactions(
    root: etree._Element,
    ns: str,
    version: str,
    af: AuditFile,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> None:
    """Parse the transactions section (journals > transactions > trLines)."""
    company_el = root.find(f"{{{ns}}}company")
    if company_el is None:
        return

    txns_el = company_el.find(f"{{{ns}}}transactions")
    if txns_el is None:
        return

    txns = Transactions(
        linesCount=_get_child_text(txns_el, "linesCount", ns) or "",
        totalDebit=_get_child_text(txns_el, "totalDebit", ns) or "",
        totalCredit=_get_child_text(txns_el, "totalCredit", ns) or "",
    )

    journal_els = txns_el.findall(f"{{{ns}}}journal")
    total_journals = len(journal_els)

    for j_idx, jrn_el in enumerate(journal_els):
        journal = Journal(
            jrnID=_get_child_text(jrn_el, "jrnID", ns) or "",
            desc=_get_child_text(jrn_el, "desc", ns) or "",
            jrnTp=_get_child_text(jrn_el, "jrnTp", ns),
            offsetAccID=_get_child_text(jrn_el, "offsetAccID", ns),
        )

        for txn_el in jrn_el.findall(f"{{{ns}}}transaction"):
            txn = Transaction(
                nr=_get_child_text(txn_el, "nr", ns) or "",
                desc=_get_child_text(txn_el, "desc", ns),
                periodNumber=_get_child_text(txn_el, "periodNumber", ns) or "",
                trDt=_get_child_text(txn_el, "trDt", ns) or "",
            )

            # Version-specific source/user fields
            if version == "4.0":
                txn.source = _get_child_text(txn_el, "Source", ns)
                txn.user = _get_child_text(txn_el, "User", ns)
            else:
                txn.source = _get_child_text(txn_el, "sourceID", ns)
                txn.user = _get_child_text(txn_el, "userID", ns)
                txn.amnt = _get_child_text(txn_el, "amnt", ns)

            for line_el in txn_el.findall(f"{{{ns}}}trLine"):
                line = _parse_tr_line(line_el, ns, version)
                txn.lines.append(line)

            journal.transactions.append(txn)

        txns.journals.append(journal)

        if progress_callback and total_journals > 0:
            pct = 70 + int((j_idx + 1) / total_journals * 25)
            progress_callback(pct, f"Parsed journal {j_idx + 1}/{total_journals}")

    af.transactions = txns


def _parse_tr_line(line_el: etree._Element, ns: str, version: str) -> TransactionLine:
    """Parse a single transaction line element."""
    line = TransactionLine(
        nr=_get_child_text(line_el, "nr", ns) or "",
        accID=_get_child_text(line_el, "accID", ns) or "",
        docRef=_get_child_text(line_el, "docRef", ns) or "",
        effDate=_get_child_text(line_el, "effDate", ns) or "",
        desc=_get_child_text(line_el, "desc", ns),
        amnt=_get_child_text(line_el, "amnt", ns) or "",
        amntTp=_get_child_text(line_el, "amntTp", ns) or "",
        custSupID=_get_child_text(line_el, "custSupID", ns),
        invRef=_get_child_text(line_el, "invRef", ns),
    )

    if version == "4.0":
        line.settDate = _get_child_text(line_el, "settDate", ns)
        line.receivingDocRef = _get_child_text(line_el, "receivingDocRef", ns)
        line.shipDocRef = _get_child_text(line_el, "shipDocRef", ns)
        line.cost = _get_child_text(line_el, "cost", ns)
        line.product = _get_child_text(line_el, "product", ns)
        line.project = _get_child_text(line_el, "project", ns)
        line.workCostArrRef = _get_child_text(line_el, "workCostArrRef", ns)
        line.bankAccNr = _get_child_text(line_el, "bankAccNr", ns)
        line.offsetBankAccNr = _get_child_text(line_el, "offsetBankAccNr", ns)
    else:
        line.cost = _get_child_text(line_el, "costID", ns)
        line.product = _get_child_text(line_el, "productID", ns)
        line.project = _get_child_text(line_el, "projectID", ns)
        line.matchKeyID = _get_child_text(line_el, "matchKeyID", ns)
        line.artGrpID = _get_child_text(line_el, "artGrpID", ns)
        line.qnttyID = _get_child_text(line_el, "qnttyID", ns)
        line.qntty = _get_child_text(line_el, "qntty", ns)

    # VAT entries (0..99)
    for vat_el in line_el.findall(f"{{{ns}}}vat"):
        line.vat.append(VatEntry(
            vatID=_get_child_text(vat_el, "vatID", ns) or "",
            vatPerc=_get_child_text(vat_el, "vatPerc", ns) or "",
            vatAmnt=_get_child_text(vat_el, "vatAmnt", ns) or "",
            vatAmntTp=_get_child_text(vat_el, "vatAmntTp", ns) or "",
        ))

    # Currency (0..1)
    cur_el = line_el.find(f"{{{ns}}}currency")
    if cur_el is not None:
        line.currency = CurrencyEntry(
            curCode=_get_child_text(cur_el, "curCode", ns) or "",
            curAmnt=_get_child_text(cur_el, "curAmnt", ns) or "",
        )

    return line
