"""Internal normalized data model for XAF files (versions 3.1, 3.2, 4.0).

These dataclasses represent the parsed XAF data in a version-agnostic form.
They can be serialized to dicts for export and storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Address:
    streetname: Optional[str] = None
    number: Optional[str] = None
    numberExtension: Optional[str] = None
    property: Optional[str] = None  # 3.x only
    city: Optional[str] = None
    postalCode: Optional[str] = None
    region: Optional[str] = None  # 3.x only
    country: Optional[str] = None


@dataclass
class BankAccount:
    """3.x only."""
    bankAccNr: str = ""
    bankIdCd: Optional[str] = None


@dataclass
class VatEntry:
    vatID: str = ""
    vatPerc: str = ""
    vatAmnt: str = ""
    vatAmntTp: str = ""


@dataclass
class CurrencyEntry:
    curCode: str = ""
    curAmnt: str = ""


@dataclass
class TransactionLine:
    nr: str = ""
    accID: str = ""
    docRef: str = ""
    effDate: str = ""
    settDate: Optional[str] = None  # 4.0 only
    desc: Optional[str] = None
    amnt: str = ""
    amntTp: str = ""
    custSupID: Optional[str] = None
    invRef: Optional[str] = None
    receivingDocRef: Optional[str] = None  # 4.0 only
    shipDocRef: Optional[str] = None  # 4.0 only
    cost: Optional[str] = None  # 4.0: cost, 3.x: costID
    product: Optional[str] = None  # 4.0: product, 3.x: productID
    project: Optional[str] = None  # 4.0: project, 3.x: projectID
    workCostArrRef: Optional[str] = None  # 4.0 only
    bankAccNr: Optional[str] = None  # 4.0 only
    offsetBankAccNr: Optional[str] = None  # 4.0 only
    matchKeyID: Optional[str] = None  # 3.x only
    artGrpID: Optional[str] = None  # 3.x only
    qnttyID: Optional[str] = None  # 3.x only
    qntty: Optional[str] = None  # 3.x only
    vat: list[VatEntry] = field(default_factory=list)
    currency: Optional[CurrencyEntry] = None


@dataclass
class Transaction:
    nr: str = ""
    desc: Optional[str] = None
    periodNumber: str = ""
    trDt: str = ""
    source: Optional[str] = None  # 4.0: Source, 3.x: sourceID
    user: Optional[str] = None  # 4.0: User, 3.x: userID
    amnt: Optional[str] = None  # 3.x only
    lines: list[TransactionLine] = field(default_factory=list)


@dataclass
class Journal:
    jrnID: str = ""
    desc: str = ""
    jrnTp: Optional[str] = None
    offsetAccID: Optional[str] = None
    transactions: list[Transaction] = field(default_factory=list)


@dataclass
class Transactions:
    linesCount: str = ""
    totalDebit: str = ""
    totalCredit: str = ""
    journals: list[Journal] = field(default_factory=list)


@dataclass
class OpeningBalanceLine:
    nr: str = ""
    accID: str = ""
    amnt: str = ""
    amntTp: str = ""


@dataclass
class OpeningBalance:
    opBalDate: Optional[str] = None  # 3.x only
    opBalDesc: Optional[str] = None  # 3.x only
    linesCount: str = ""
    totalDebit: str = ""
    totalCredit: str = ""
    lines: list[OpeningBalanceLine] = field(default_factory=list)


@dataclass
class Period:
    periodNumber: str = ""
    periodDesc: Optional[str] = None  # 3.x only
    startDatePeriod: str = ""
    endDatePeriod: str = ""
    startTimePeriod: Optional[str] = None  # 3.x only
    endTimePeriod: Optional[str] = None  # 3.x only


@dataclass
class VatCode:
    vatID: str = ""
    vatDesc: str = ""
    vatToPayAccID: Optional[str] = None
    vatToClaimAccID: Optional[str] = None


@dataclass
class LedgerAccount:
    accID: str = ""
    accDesc: str = ""
    accTp: str = ""
    rgsCode: Optional[str] = None  # 4.0 only
    leadCode: Optional[str] = None  # 3.x only
    leadDescription: Optional[str] = None  # 3.x only
    leadReference: Optional[str] = None  # 3.x only
    leadCrossRef: Optional[str] = None  # 3.x only


@dataclass
class CustomerSupplier:
    custSupID: str = ""
    custSupName: Optional[str] = None
    contact: Optional[str] = None  # 3.x only
    telephone: Optional[str] = None  # 3.x only
    fax: Optional[str] = None  # 3.x only
    eMail: Optional[str] = None
    website: Optional[str] = None  # 3.x only
    commerceNr: Optional[str] = None
    taxRegistrationCountry: Optional[str] = None
    taxRegIdent: Optional[str] = None
    relationshipID: Optional[str] = None  # 3.x only
    custSupTp: Optional[str] = None
    custSupGrpID: Optional[str] = None  # 3.x only
    custCreditLimit: Optional[str] = None  # 3.x only
    supplierLimit: Optional[str] = None  # 3.x only
    opBalDesc: Optional[str] = None
    opBalTp: Optional[str] = None
    clBalDesc: Optional[str] = None
    clBalTp: Optional[str] = None
    streetAddresses: list[Address] = field(default_factory=list)
    postalAddresses: list[Address] = field(default_factory=list)  # 3.x only
    bankAccounts: list[BankAccount] = field(default_factory=list)  # 3.x only


@dataclass
class Header:
    fiscalYear: str = ""
    startDate: str = ""
    endDate: str = ""
    curCode: str = ""
    dateCreated: str = ""
    softwareDesc: str = ""
    softwareVersion: str = ""
    rgsVersion: Optional[str] = None  # 4.0 only
    auditfileVersion: Optional[str] = None  # 3.x only
    softwareID: Optional[str] = None  # 3.x only


@dataclass
class Company:
    companyIdent: Optional[str] = None  # 3.x
    commerceNr: Optional[str] = None  # 4.0
    companyName: str = ""
    taxRegistrationCountry: str = ""
    taxRegIdent: str = ""
    streetAddresses: list[Address] = field(default_factory=list)
    postalAddresses: list[Address] = field(default_factory=list)  # 3.x only


@dataclass
class AuditFile:
    sourceVersion: str = ""
    sourceNamespace: str = ""
    header: Header = field(default_factory=Header)
    company: Company = field(default_factory=Company)
    customersSuppliers: list[CustomerSupplier] = field(default_factory=list)
    ledgerAccounts: list[LedgerAccount] = field(default_factory=list)
    vatCodes: list[VatCode] = field(default_factory=list)
    periods: list[Period] = field(default_factory=list)
    openingBalance: Optional[OpeningBalance] = None
    transactions: Optional[Transactions] = None


def audit_file_to_dict(af: AuditFile) -> dict:
    """Convert an AuditFile to a plain dict, stripping None values recursively."""
    return asdict(af)
