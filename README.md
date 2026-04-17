# XAF Converter

Convert Dutch XAF (XML Auditfile Financieel) files to CSV, XLSX, JSON, and Parquet.

XAF Converter is a self-hosted web application that runs entirely in Docker. Upload an XAF file from any accounting system (Exact Online, Twinfield, AFAS, and others), preview the data, select what you need, and export it. All data stays within your own infrastructure.

## Features

- **XAF 3.1, 3.2, and 4.0** support
- **Export formats**: CSV, XLSX (styled), JSON, Parquet
- **Data preview** with search across all records
- **Data integrity verification** against XAF control totals
- **XLSX validation tab** embedded in exports for audit trail
- **Dark and light mode** with system preference detection
- **No external dependencies** at runtime - everything runs locally in Docker
- **Session-based** - parse once, export multiple times

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine

If you don't have Docker yet, download it from [docker.com](https://docs.docker.com/get-docker/). It's available for Windows, Mac, and Linux. After installing, make sure Docker is running (you'll see the Docker icon in your system tray or menu bar).

### Step 1: Get the code

```bash
git clone https://github.com/YOUR_USERNAME/xaf-converter.git
cd xaf-converter
```

### Step 2: Build the Docker image

This builds the application into a single Docker container. It may take a few minutes the first time.

```bash
docker build -t xaf-converter .
```

### Step 3: Start the application

```bash
docker run -d --name xaf-converter -p 8080:80 xaf-converter
```

### Step 4: Open in your browser

Go to [http://localhost:8080](http://localhost:8080)

That's it! You can now upload XAF files and export them.

### Stopping and restarting

```bash
# Stop the application
docker stop xaf-converter

# Start it again
docker start xaf-converter

# Remove the container (to rebuild or clean up)
docker stop xaf-converter
docker rm xaf-converter
```

### Using a different port

If port 8080 is already in use, pick another port (e.g. 3000):

```bash
docker run -d --name xaf-converter -p 3000:80 xaf-converter
```

Then open [http://localhost:3000](http://localhost:3000).

### Updating to a new version

```bash
docker stop xaf-converter
docker rm xaf-converter
git pull
docker build -t xaf-converter .
docker run -d --name xaf-converter -p 8080:80 xaf-converter
```

## How it works

1. **Upload** a `.xaf` or `.xml` file (up to 250 MB)
2. The file is parsed and **validated** against the XAF's built-in control totals (line counts, debit/credit sums)
3. **Select** which data types to export (general ledger, transactions, customers/suppliers, etc.)
4. **Preview** the data with full-text search
5. **Export** to your preferred format
6. You can re-export in different formats without re-uploading

## Data types

Depending on the XAF file, the following data types may be available:

| Data Type | Description |
|---|---|
| Header | Fiscal year, dates, currency, software info |
| Company | Company name, address, tax registration |
| Customers & Suppliers | Debtors and creditors with balances |
| General Ledger | Chart of accounts |
| VAT Codes | VAT code definitions |
| Periods | Booking periods |
| Opening Balance | Opening balance lines |
| Transaction Lines | All journal entries (the bulk of the data) |

## Export formats

| Format | Details |
|---|---|
| **XLSX** | One tab per data type, styled headers, auto-width columns, validation tab |
| **CSV** | One file per data type (zipped if multiple selected), formula-injection safe |
| **JSON** | Structured object with data types as keys |
| **Parquet** | One file per data type (zipped if multiple), typed columns |

## Security

- Runs as a non-root user inside the container
- XML parsing uses defusedxml to prevent XXE attacks
- All file paths are validated to prevent path traversal
- Client-supplied filenames are replaced with UUIDs
- CSV output uses QUOTE_ALL to prevent formula injection
- No data is sent to external services
- Sessions expire after 1 hour and all data is deleted

## Privacy

XAF Converter is designed to be **self-hosted**. Your financial data never leaves your server. The application runs entirely within your Docker instance with no outbound network calls.

## Development

### Running locally (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on port 3000 and proxies API requests to port 8000.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

An [Endeavors](https://www.endeavors.nl) initiative.
