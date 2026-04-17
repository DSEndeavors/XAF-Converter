# XAF (XML Auditfile Financieel) Data Model

> Reference document for the XAF Converter parser. Covers versions 3.1, 3.2, and 4.0.
> Generated from official XSD schemas, functional hierarchy documents, and revision PDFs
> published by the Belastingdienst / XML Platform.

---

## 1. Version Overview

| Property | XAF 3.1 | XAF 3.2 | XAF 4.0 |
|---|---|---|---|
| **Release** | ~2009 | 2014 (revised Sept 2017) | Feb 2025 |
| **Namespace URI** | `http://www.auditfiles.nl/XAF/3.1` | `http://www.auditfiles.nl/XAF/3.2` | `http://www.odb.belastingdienst.nl/Belastingdienst/BCPP/1.1/structures/XmlauditfileXAF_4.0` |
| **Total fields** | ~200 (est.) | ~250 | 90 |
| **Character sets** | UTF-8, ISO-8859-1 | UTF-8, ISO-8859-1 | UTF-8, ISO-8859-1 |
| **File extension** | .xaf / .xml | .xaf / .xml | .XAF / .xml |

### Key design philosophy change (3.2 -> 4.0)

XAF 4.0 is a **major simplification** from 3.2. The field count dropped from ~250 to 90.
The reduction was driven by:
- Removal of **history tracking** structures (changeInfo, customerSupplierHistory, ledgerAccountHistory)
- Removal of **subledger** structures (obSubledgers, subledger, subledgerLine)
- Removal of **postal address** (only streetAddress remains)
- Removal of **bank account** from customerSupplier
- Removal of **basics** / taxonomy / entry point / domain member from generalLedger
- Removal of several customerSupplier fields (contact, telephone, fax, website, relationshipID, custSupGrpID, custCreditLimit, supplierLimit)
- Simplification of RGS linkage (single `RGScode` field on ledgerAccount instead of taxonomy tree)
- Changed company identifier from `companyIdent` to `Commercenr` (KvK number)

---

## 2. Document Hierarchy

All versions share the same top-level structure:

```
auditfile
  +-- header                          1..1, Required
  +-- company                         1..1, Required
        +-- streetAddress             0..*, Optional
        +-- postalAddress             0..*, Optional  [3.1/3.2 only]
        +-- customersSuppliers        0..1, Optional
        |     +-- customerSupplier    0..*, Optional
        |           +-- streetAddress 0..*, Optional
        |           +-- postalAddress 0..*, Optional  [3.1/3.2 only]
        |           +-- bankAccount   0..*, Optional  [3.1/3.2 only]
        |           +-- changeInfo    0..1, Optional  [3.2 only]
        |           +-- customerSupplierHistory  0..1 [3.2 only]
        +-- generalLedger            0..1, Optional
        |     +-- ledgerAccount      1..*, Required (if parent present)
        |           +-- taxonomy     0..*, Optional  [3.2 only]
        |           +-- changeInfo   0..1, Optional  [3.2 only]
        |           +-- glAccountHistory 0..1        [3.2 only]
        |     +-- basics             0..1, Optional  [3.2 only]
        +-- vatCodes                 0..1, Optional
        |     +-- vatCode            0..*, Optional
        +-- periods                  0..1, Optional
        |     +-- period             0..*, Optional
        +-- openingBalance           0..1, Optional
        |     +-- obLine             0..*, Optional
        |     +-- obSubledgers       0..1, Optional  [3.2 only]
        +-- transactions             0..1, Optional
              +-- journal            0..*, Optional
                    +-- transaction  0..*, Optional
                          +-- trLine 0..*, Optional
                                +-- vat      0..99, Optional
                                +-- currency 0..1, Optional
```

---

## 3. Sections - Field-level Detail

### 3.1 Header (`header`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `fiscalYear` | Fiscal year (YYYY or YYYY-YYYY for broken book year) | R | R | R | string, max 9, pattern `\d{4}\|\(\d{4}\-\d{4}\)` |
| `startDate` | Start date of booking period | R | R | R | xsd:date (YYYY-MM-DD) |
| `endDate` | End date of booking period | R | R | R | xsd:date |
| `curCode` | Currency code (ISO 4217) | R | R | R | string, max 3 |
| `dateCreated` | Date the auditfile was created | R | R | R | xsd:date |
| `softwareDesc` | Software name that generated the file | R | R | R | string, max 50 |
| `softwareVersion` | Software version | R | R | R | string, max 20 |
| `RGSVersion` | RGS (Referentie Grootboekschema) version | - | - | O | string, max 20 |
| `auditfileVersion` | Version identifier of the auditfile format | R | R | - | string |
| `softwareID` | Software identifier | O | O | - | string |

**Notes:**
- In 3.1/3.2 the `auditfileVersion` field is present in the header. In 4.0, version is determined by namespace.
- `RGSVersion` is new in 4.0 to support RGS linkage at header level.

### 3.2 Company (`company`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `companyIdent` | Company administration number | R | R | - | string, max 35 |
| `Commercenr` | KvK (Chamber of Commerce) number | - | - | O | string, max 100 |
| `companyName` | Legal name of the company | R | R | R | string, max 255 (3.2: max 999) |
| `taxRegistrationCountry` | ISO 3166 country code | R | R | R | string, length 2 |
| `taxRegIdent` | Tax registration number (BTW-id) | R | R | R | string, max 30 |

**Key change:** `companyIdent` (internal admin number) was replaced by `Commercenr` (KvK number) in 4.0. The `companyIdent` was required in 3.2 but `Commercenr` is optional in 4.0.

### 3.3 Street Address (`streetAddress`)

Used for both company and customerSupplier addresses.

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `streetname` | Street name | O | O | O | string, max 100 (3.2: max 999) |
| `number` | House number | O | O | O | string, max 15 |
| `numberExtension` | House number addition | O | O | O | string, max 999 (3.2: max 50) |
| `property` | Building or company name | O | O | - | string, max 50 |
| `city` | City | O | O | O | string, max 50 |
| `postalCode` | Postal code | O | O | O | string, max 10 |
| `region` | Province/region | O | O | - | string, max 50 |
| `country` | ISO 3166 country code | O | O | O | string, length 2 |

**Changes in 4.0:**
- `property` field removed
- `region` field removed
- `streetname` max length reduced from 999 to 100
- `numberExtension` max length changed (was 50 in 3.2 -> 999 in 4.0)

### 3.4 Postal Address (`postalAddress`) -- 3.1/3.2 ONLY

Same fields as streetAddress. **Entirely removed in 4.0.**

### 3.5 Customers/Suppliers (`customersSuppliers` > `customerSupplier`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `custSupID` | Unique debtor/creditor ID | R | R | R | string, max 35 |
| `custSupName` | Legal name | O | O | O | string, max 50 |
| `contact` | Contact person | O | O | - | string, max 50 |
| `telephone` | Phone number | O | O | - | string, max 30 |
| `fax` | Fax number | O | O | - | string, max 30 |
| `eMail` | Email address | O | O | O | token (4.0) / string, max 255 |
| `website` | URL | O | O | - | string, max 255 |
| `commerceNr` | KvK number | - | O | O | string, max 100 (3.2: max 999) |
| `taxRegistrationCountry` | ISO 3166 country code | O | O | O | string, length 2 |
| `taxRegIdent` | Tax registration number | O | O | O | string, max 30 |
| `relationshipID` | Relationship type code | O | O | - | string, max 35 |
| `custSupTp` | Customer/Supplier type | O | O | O | enum: B/C/S (4.0), B/C/O/S (3.2) |
| `custSupGrpID` | Customer/supplier group | O | O | - | string, max 35 |
| `custCreditLimit` | Customer credit limit | O | O | - | decimal(20,2) |
| `supplierLimit` | Supplier limit | O | O | - | decimal(20,2) |
| `opBalDesc` | Opening balance amount | O | O | O | decimal(20,2) |
| `opBalTp` | Opening balance D/C | O | O | O | enum: C/D |
| `clBalDesc` | Closing balance amount | - | O | O | decimal(20,2) |
| `clBalTp` | Closing balance D/C | - | O | O | enum: C/D |

**`custSupTp` code list:**

| Code | Meaning | 3.1 | 3.2 | 4.0 |
|---|---|---|---|---|
| B | Both Customer and Supplier | Y | Y | Y |
| C | Customer | Y | Y | Y |
| S | Supplier | Y | Y | Y |
| O | Other, no Customer or Supplier | - | Y | - |

**Removed in 4.0:** contact, telephone, fax, website, relationshipID, custSupGrpID, custCreditLimit, supplierLimit, bankAccount section, changeInfo section, customerSupplierHistory section

### 3.6 Bank Account (`bankAccount`) -- 3.1/3.2 ONLY

| XML Tag | Description | 3.1 | 3.2 | Type |
|---|---|---|---|---|
| `bankAccNr` | Bank account number (IBAN) | R | R | string, max 35 |
| `bankIdCd` | BIC code | O | O | string, max 35 |

**Entirely removed from customerSupplier in 4.0.**

### 3.7 General Ledger (`generalLedger` > `ledgerAccount`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `accID` | Unique account code | R | R | R | string, max 35 |
| `accDesc` | Account description | R | R | R | string, max 255 (3.2: max 999) |
| `accTp` | Account type | R | R | R | enum (see below) |
| `leadCode` | Lead code | O | O | - | string, max 999 |
| `leadDescription` | Lead description | O | O | - | string, max 999 |
| `leadReference` | Lead reference | O | O | - | string, max 999 |
| `leadCrossRef` | Lead cross reference | O | O | - | string, max 999 |
| `RGScode` | RGS code linked to account | - | - | O | string, max 255 |

**`accTp` (Account Type) code list:**

| Code | Meaning | 3.1 | 3.2 | 4.0 |
|---|---|---|---|---|
| B | Balance | Y | Y | Y |
| P | Profit and Loss | Y | Y | Y |
| M | Mixed | Y | Y | - |

**Removed in 4.0:** leadCode, leadDescription, leadReference, leadCrossRef, taxonomy (with entryPoint/domainMember), changeInfo, glAccountHistory, basics section. `M` (Mixed) account type removed.

**New in 4.0:** `RGScode` field (replaces the complex taxonomy structure from 3.2)

### 3.8 VAT Codes (`vatCodes` > `vatCode`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `vatID` | Unique VAT code | R | R | R | string, max 35 |
| `vatDesc` | VAT code description | R | R | R | string, max 100 (3.2: max 999) |
| `vatToPayAccID` | GL account for VAT payable | O | O | O | string, max 35 |
| `vatToClaimAccID` | GL account for VAT receivable | O | O | O | string, max 35 |

This section is **identical in structure** across all versions. Only max lengths differ slightly.

### 3.9 Periods (`periods` > `period`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `periodNumber` | Period number | R | R | R | nonNegativeInteger, max 3 digits |
| `periodDesc` | Period description | O | O | - | string, max 50 |
| `startDatePeriod` | Period start date | R | R | R | xsd:date |
| `endDatePeriod` | Period end date | R | R | R | xsd:date |
| `startTimePeriod` | Period start time | O | O | - | xsd:time |
| `endTimePeriod` | Period end time | O | O | - | xsd:time |

**Removed in 4.0:** `periodDesc`, `startTimePeriod`, `endTimePeriod`

### 3.10 Opening Balance (`openingBalance`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `opBalDate` | Opening balance date | O | O | - | xsd:date |
| `opBalDesc` | Opening balance description | O | O | - | string, max 999 |
| `linesCount` | Number of opening balance lines | R | R | R | nonNegativeInteger, max 10 digits |
| `totalDebit` | Total debit amount | R | R | R | decimal(20,2) |
| `totalCredit` | Total credit amount | R | R | R | decimal(20,2) |

**Validation rules:**
- `[0004]` totalDebit = SUM(obLine/amnt) where amntTp = "D"
- `[0005]` totalCredit = SUM(obLine/amnt) where amntTp = "C"
- `[0006]` totalDebit = totalCredit

#### Opening Balance Line (`obLine`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `nr` | Line number | R | R | R | string, max 35 |
| `accID` | GL account code | R | R | R | string, max 35 |
| `amnt` | Amount in local currency | R | R | R | decimal(20,2) |
| `amntTp` | Debit/Credit indicator | R | R | R | enum: C/D |

**Removed in 4.0:** Entire `obSubledgers` section (subledger opening balances with sbType, obSbLine etc.)

### 3.11 Transactions (`transactions`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `linesCount` | Total transaction line count | R | R | R | nonNegativeInteger, max 10 digits |
| `totalDebit` | Total debit | R | R | R | decimal(20,2) |
| `totalCredit` | Total credit | R | R | R | decimal(20,2) |

**Validation rules:**
- `[0007]` totalDebit = SUM(journal/transaction/trLine/amnt) where amntTp = "D"
- `[0008]` totalCredit = SUM(journal/transaction/trLine/amnt) where amntTp = "C"
- `[0009]` totalDebit = totalCredit

#### Journal (`journal`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `jrnID` | Unique journal code | R | R | R | string, max 35 |
| `desc` | Journal description | R | R | R | string, unbounded (4.0: TypeString9999) |
| `jrnTp` | Journal type | O | O | O | enum (see below) |
| `offsetAccID` | Default offset account | O | O | O | string, max 35 |

**`jrnTp` (Journal Type) code list:**

| Code | Meaning |
|---|---|
| B | Bank |
| C | Cash |
| G | Goods (received/sent) |
| M | Memo / Daybook |
| O | Other (4.0 only) |
| P | Purchases |
| S | Sales |
| T | Production |
| Y | Payroll |
| Z | Other (legacy) |

#### Transaction (`transaction`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `nr` | Transaction number (unique within journal) | R | R | R | string, max 35 |
| `desc` | Transaction description | O | O | O | string, unbounded |
| `periodNumber` | Period reference | R | R | R | nonNegativeInteger, max 3 digits |
| `trDt` | Transaction/booking date | R | R | R | xsd:date |
| `Source` | Source application identifier | - | - | O | string, max 999 |
| `User` | User who created the transaction | - | - | O | string, max 999 |
| `amnt` | Transaction amount | O | O | - | decimal(20,2) |
| `sourceID` | Source identifier | O | O | - | string |
| `userID` | User identifier | O | O | - | string, max 35 |

**Note:** In 4.0, `Source` and `User` replace the old `sourceID`/`userID` fields with different casing and increased max length.

**Validation rule:**
- `[0010]` SUM(trLine/amnt where amntTp="D") = SUM(trLine/amnt where amntTp="C") per transaction

#### Transaction Line (`trLine`)

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `nr` | Line number (unique within transaction) | R | R | R | string, max 35 |
| `accID` | GL account code | R | R | R | string, max 35 |
| `docRef` | Document reference | R | R | R | string, max 255 |
| `effDate` | Effective date (invoice date) | R | R | R | xsd:date |
| `settDate` | Settlement/delivery date | - | - | O | xsd:date |
| `desc` | Line description | O | O | O | string, unbounded |
| `amnt` | Amount in local currency | R | R | R | decimal(20,2) |
| `amntTp` | Debit/Credit indicator | R | R | R | enum: C/D |
| `custSupID` | Customer/Supplier reference | O | O | O | string, max 35 |
| `invRef` | Invoice reference | O | O | O | string, max 255 |
| `receivingDocRef` | Receiving document reference | - | - | O | string, max 255 |
| `shipDocRef` | Shipment document reference | - | - | O | string, max 255 |
| `cost` | Cost center | - | - | O | string, max 999 |
| `product` | Product reference | - | - | O | string, max 999 |
| `project` | Project reference | - | - | O | string, max 999 |
| `workCostArrRef` | WKR (werkkostenregeling) reference | - | - | O | string, max 255 |
| `bankAccNr` | Own bank account number | - | - | O | string, max 35 |
| `offsetBankAccNr` | Counterparty bank account number | - | - | O | string, max 35 |
| `matchKeyID` | Match key for reconciliation | O | O | - | string, max 35 |
| `costID` | Cost center ID | O | O | - | string |
| `productID` | Product ID | O | O | - | string |
| `projectID` | Project ID | O | O | - | string |
| `artGrpID` | Article group ID | O | O | - | string |
| `qnttyID` | Quantity ID | O | O | - | string |
| `qntty` | Quantity | O | O | - | decimal |

**New in 4.0:** `settDate`, `receivingDocRef`, `shipDocRef`, `cost`, `product`, `project`, `workCostArrRef`, `bankAccNr`, `offsetBankAccNr`

**Removed in 4.0:** `matchKeyID`, `costID`, `productID`, `projectID`, `artGrpID`, `qnttyID`, `qntty`

**Note:** The dimension references (cost, product, project) changed from ID-based (`costID`) to free-text (`cost`) in 4.0.

#### VAT on Transaction Line (`vat`) -- 0..99 per trLine

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `vatID` | VAT code reference | R | R | R | string, max 35 |
| `vatPerc` | VAT percentage | R | R | R | decimal(8,3) |
| `vatAmnt` | VAT amount | R | R | R | decimal(20,2) |
| `vatAmntTp` | VAT amount D/C | R | R | R | enum: C/D |

Identical structure across all versions.

#### Currency on Transaction Line (`currency`) -- 0..1 per trLine

| XML Tag | Description | 3.1 | 3.2 | 4.0 | Type |
|---|---|---|---|---|---|
| `curCode` | Foreign currency code (ISO 4217) | R | R | R | string, max 3 |
| `curAmnt` | Amount in foreign currency | R | R | R | decimal(20,2) |

Identical structure across all versions.

---

## 4. XAF 3.2-Only Structures (Removed in 4.0)

These sections exist only in XAF 3.2 and must be parsed when reading 3.2 files, but have no equivalent in 4.0.

### 4.1 Change Information (`changeInfo`)
Appeared under: customerSupplier, ledgerAccount, and their history variants.

| XML Tag | Type |
|---|---|
| `userID` | string, max 35 |
| `changeDateTime` | string, max 24 |
| `changeDescription` | string, max 999 |

### 4.2 Customer Supplier History (`customerSupplierHistory`)
Contains historical snapshots of customerSupplier records, each with the same fields as customerSupplier plus changeInfo.

### 4.3 Ledger Account History (`glAccountHistory`)
Contains historical snapshots of ledgerAccount records plus changeInfo.

### 4.4 Taxonomy / Entry Point / Domain Member
Under `ledgerAccount > taxonomy`:

| XML Tag | Description |
|---|---|
| `taxoRef` | Reference to taxonomy (RGS namespace URI) |
| `entryPoint > entryPointRef` | Entry point reference |
| `entryPoint > conceptRef` | Concept reference (e.g. RGS concept name) |
| `entryPoint > domainMember > domainMemberRef` | Domain member reference |

### 4.5 Basics (`basics` > `basic`)
Master data reference table under generalLedger:

| XML Tag | Description |
|---|---|
| `basicType` | Type code: 02=Cost, 03=Product, 04=Project, 05=ArticleGroup, 12=Journal, 14=Quantity, 23=Relationship, 29=Source, 30=User |
| `basicID` | Key value |
| `basicDesc` | Description |

### 4.6 Subledgers (`openingBalance > obSubledgers > obSubledger`)
Sub-ledger opening balances:

| XML Tag | Description |
|---|---|
| `sbType` | Subledger type: CS/CU/SU/ZZ |
| `sbDesc` | Description |
| `linesCount` | Line count |
| `totalDebit` / `totalCredit` | Totals |
| `obSbLine > nr` | Line number |
| `obSbLine > obLineNr` | Reference to parent obLine |
| `obSbLine > desc` | Description |
| `obSbLine > amnt` / `amntTp` | Amount and D/C |
| `obSbLine > docRef` | Document reference |
| `obSbLine > recRef` | Reconciliation reference |
| `obSbLine > matchKeyID` | Match key |
| `obSbLine > custSupID` | Customer/Supplier reference |

---

## 5. XAF Custom Types Reference (from 4.0 XSD)

| XSD Type Name | Base | Constraints |
|---|---|---|
| `TypeAmount2decimals` | xsd:decimal | totalDigits=20, fractionDigits=2 |
| `TypeCountrycodeIso3166` | xsd:string | length=2, pattern `\D*` |
| `TypeCurrencycodeIso4217` | xsd:string | maxLength=3, pattern `\D*` |
| `TypeCustomersuppliercode` | xsd:string | length=1, enum: B/C/S |
| `TypeDebitcredittype` | xsd:string | length=1, enum: C/D |
| `TypeDecimal8` | xsd:decimal | totalDigits=8, fractionDigits=3, minInclusive=0 |
| `TypeIdentificationString35` | xsd:string | maxLength=35 |
| `TypeJournaltype` | xsd:string | maxLength=2, enum: B/C/G/M/O/P/S/T/Y/Z |
| `TypeNonnegativeinteger10` | xsd:nonNegativeInteger | totalDigits=10 |
| `TypeNonnegativeinteger3` | xsd:nonNegativeInteger | totalDigits=3 |
| `TypeString9` | xsd:string | maxLength=9, pattern `\d{4}\|(\d{4}\-\d{4})` |
| `TypeString9999` | xsd:string | (unbounded) |
| `accTp` | xsd:string | maxLength=2, enum: B/P |

---

## 6. XAF 3.1 Notes

XAF 3.1 uses namespace `http://www.auditfiles.nl/XAF/3.1` and is structurally very similar to 3.2 but with:
- Fewer optional fields on customerSupplier (no `clBalDesc`/`clBalTp`)
- No `commerceNr` on customerSupplier
- Original `leadCode`-based structure for GL accounts (no taxonomy/RGS yet)
- No `changeInfo` or history sections
- Slightly smaller max field lengths in some cases

For parser purposes, 3.1 can be treated as a **subset of 3.2** -- any valid 3.1 file can be parsed using 3.2 logic with appropriate null handling.

---

## 7. Proposed Normalized Internal Data Model

This model can represent any XAF version (3.1, 3.2, 4.0) without data loss.

### 7.1 Top-Level Container

```
AuditFile {
  sourceVersion: "3.1" | "3.2" | "4.0"
  sourceNamespace: string
  header: Header
  company: Company
}
```

### 7.2 Header

```
Header {
  fiscalYear: string            // "2024" or "2023-2024"
  startDate: date
  endDate: date
  curCode: string               // ISO 4217
  dateCreated: date
  softwareDesc: string
  softwareVersion: string
  rgsVersion: string?           // 4.0 only
  auditfileVersion: string?     // 3.x only
  softwareID: string?           // 3.x only
}
```

### 7.3 Company

```
Company {
  companyIdent: string?         // 3.x: companyIdent, 4.0: null
  commerceNr: string?           // 4.0: Commercenr, 3.x: null
  companyName: string
  taxRegistrationCountry: string  // ISO 3166
  taxRegIdent: string
  streetAddresses: Address[]
  postalAddresses: Address[]    // 3.x only, empty for 4.0
  customersSuppliers: CustomerSupplier[]
  ledgerAccounts: LedgerAccount[]
  vatCodes: VatCode[]
  periods: Period[]
  openingBalance: OpeningBalance?
  transactions: Transactions?
}
```

### 7.4 Address

```
Address {
  streetname: string?
  number: string?
  numberExtension: string?
  property: string?             // 3.x only
  city: string?
  postalCode: string?
  region: string?               // 3.x only
  country: string?              // ISO 3166
}
```

### 7.5 CustomerSupplier

```
CustomerSupplier {
  custSupID: string
  custSupName: string?
  contact: string?              // 3.x only
  telephone: string?            // 3.x only
  fax: string?                  // 3.x only
  eMail: string?
  website: string?              // 3.x only
  commerceNr: string?
  taxRegistrationCountry: string?
  taxRegIdent: string?
  relationshipID: string?       // 3.x only
  custSupTp: "B" | "C" | "S" | "O" | null
  custSupGrpID: string?         // 3.x only
  custCreditLimit: decimal?     // 3.x only
  supplierLimit: decimal?       // 3.x only
  opBalDesc: decimal?
  opBalTp: "C" | "D" | null
  clBalDesc: decimal?
  clBalTp: "C" | "D" | null
  streetAddresses: Address[]
  postalAddresses: Address[]    // 3.x only
  bankAccounts: BankAccount[]   // 3.x only
}
```

### 7.6 BankAccount (3.x only)

```
BankAccount {
  bankAccNr: string
  bankIdCd: string?
}
```

### 7.7 LedgerAccount

```
LedgerAccount {
  accID: string
  accDesc: string
  accTp: "B" | "P" | "M"       // M only in 3.x
  rgsCode: string?              // 4.0: RGScode field
  leadCode: string?             // 3.x only
  leadDescription: string?      // 3.x only
  leadReference: string?        // 3.x only
  leadCrossRef: string?         // 3.x only
}
```

### 7.8 VatCode

```
VatCode {
  vatID: string
  vatDesc: string
  vatToPayAccID: string?
  vatToClaimAccID: string?
}
```

### 7.9 Period

```
Period {
  periodNumber: int
  periodDesc: string?           // 3.x only
  startDatePeriod: date
  endDatePeriod: date
  startTimePeriod: time?        // 3.x only
  endTimePeriod: time?          // 3.x only
}
```

### 7.10 OpeningBalance

```
OpeningBalance {
  opBalDate: date?              // 3.x only
  opBalDesc: string?            // 3.x only
  linesCount: int
  totalDebit: decimal
  totalCredit: decimal
  lines: OpeningBalanceLine[]
}
```

### 7.11 OpeningBalanceLine

```
OpeningBalanceLine {
  nr: string
  accID: string
  amnt: decimal
  amntTp: "C" | "D"
}
```

### 7.12 Transactions

```
Transactions {
  linesCount: int
  totalDebit: decimal
  totalCredit: decimal
  journals: Journal[]
}
```

### 7.13 Journal

```
Journal {
  jrnID: string
  desc: string
  jrnTp: string?                // B/C/G/M/O/P/S/T/Y/Z
  offsetAccID: string?
  transactions: Transaction[]
}
```

### 7.14 Transaction

```
Transaction {
  nr: string
  desc: string?
  periodNumber: int
  trDt: date
  source: string?               // 4.0: Source, 3.x: sourceID
  user: string?                 // 4.0: User, 3.x: userID
  amnt: decimal?                // 3.x only
  lines: TransactionLine[]
}
```

### 7.15 TransactionLine

```
TransactionLine {
  nr: string
  accID: string
  docRef: string
  effDate: date
  settDate: date?               // 4.0 only
  desc: string?
  amnt: decimal
  amntTp: "C" | "D"
  custSupID: string?
  invRef: string?
  receivingDocRef: string?      // 4.0 only
  shipDocRef: string?           // 4.0 only
  cost: string?                 // 4.0: cost, 3.x: costID
  product: string?              // 4.0: product, 3.x: productID
  project: string?              // 4.0: project, 3.x: projectID
  workCostArrRef: string?       // 4.0 only (WKR)
  bankAccNr: string?            // 4.0 only
  offsetBankAccNr: string?      // 4.0 only
  matchKeyID: string?           // 3.x only
  artGrpID: string?             // 3.x only
  qnttyID: string?              // 3.x only
  qntty: decimal?               // 3.x only
  vat: VatEntry[]               // 0..99
  currency: CurrencyEntry?      // 0..1
}
```

### 7.16 VatEntry

```
VatEntry {
  vatID: string
  vatPerc: decimal
  vatAmnt: decimal
  vatAmntTp: "C" | "D"
}
```

### 7.17 CurrencyEntry

```
CurrencyEntry {
  curCode: string               // ISO 4217
  curAmnt: decimal
}
```

---

## 8. Version Detection Strategy

The parser should detect the version by examining the namespace declaration on the root `<auditfile>` element:

| Namespace | Version |
|---|---|
| `http://www.auditfiles.nl/XAF/3.1` | 3.1 |
| `http://www.auditfiles.nl/XAF/3.2` | 3.2 |
| `http://www.odb.belastingdienst.nl/Belastingdienst/BCPP/1.1/structures/XmlauditfileXAF_4.0` | 4.0 |

Additionally, 3.x files may contain `<auditfileVersion>` in the header as a secondary check.

---

## 9. Field Mapping: 3.x to 4.0 Renames

When converting between versions, these field name changes must be handled:

| 3.x Field | 4.0 Field | Notes |
|---|---|---|
| `companyIdent` | `Commercenr` | Different semantics: admin nr vs KvK nr |
| `sourceID` (transaction) | `Source` | Case change + max length increase |
| `userID` (transaction) | `User` | Case change + max length increase |
| `costID` (trLine) | `cost` | ID reference -> free text |
| `productID` (trLine) | `product` | ID reference -> free text |
| `projectID` (trLine) | `project` | ID reference -> free text |
| `leadCode` (ledgerAccount) | `RGScode` | Different RGS linking mechanism |
| `custCreditLimit` (custSup) | `opBalDesc` | Semantics differ: credit limit vs opening balance |
| `supplierLimit` (custSup) | `clBalDesc` | Semantics differ: credit limit vs closing balance |

---

## 10. References

- XSD Schema: `XmlAuditfileFinancieel4.0.xsd`
- Functional Hierarchy: `XMLAuditfileFinancieel_4.0_FunHie.pdf`
- Revision document: `XMLAuditfileXAF_4.0_met_revisie_naar_XAF_3.2.pdf`
- Toelichting: `XMLAuditfileFinancieelVersie_4.0_Toelichting.pdf`
- Official download: https://odb.belastingdienst.nl/auditfiles/
