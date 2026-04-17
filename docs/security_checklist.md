# XAF Converter Security Checklist

Run through this checklist after every code change. Items marked **(CI)** are automated in CI; the rest require manual review.

---

## XML Parsing

- [ ] All XML parsing uses `defusedxml` or `lxml` with `resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False`
- [ ] No use of `xml.etree.ElementTree.parse()`, `lxml.etree.parse()` with default parser, or `xml.sax` without feature disabling
- [ ] XXE integration test exists and passes **(CI)**
- [ ] Billion-laughs / entity expansion test exists and passes **(CI)**

## File Upload

- [ ] nginx `client_max_body_size` is set to `250m`
- [ ] FastAPI checks `Content-Length` header before reading the body
- [ ] Only `.xaf` and `.xml` extensions are accepted (case-insensitive)
- [ ] Client-supplied filenames are never used for file storage; UUIDs are used instead
- [ ] Upload content is validated to start with an XML declaration
- [ ] Parsing timeout of 60 seconds is enforced

## Path Traversal

- [ ] All file paths are resolved through `safe_path()` which checks against the base temp directory
- [ ] Session IDs are validated as UUID format before use in paths
- [ ] No user input is passed directly to `open()`, `os.path.join()`, or `pathlib.Path()`
- [ ] `os.path.realpath()` is used to resolve symlinks before path prefix checks

## Export Safety

- [ ] CSV output uses `csv.QUOTE_ALL` or prefixes formula-trigger characters (`=`, `+`, `-`, `@`) with `'`
- [ ] XLSX uses `openpyxl` with explicit cell types; no macros
- [ ] JSON uses `json.dumps(ensure_ascii=True)`
- [ ] Parquet uses an explicit `pyarrow` schema (no schema inference)
- [ ] All string values are stripped of null bytes and control characters
- [ ] Field values are truncated at 50,000 characters

## Response Headers

- [ ] `Content-Security-Policy` header is set; `script-src` does not contain `'unsafe-inline'`
- [ ] `X-Content-Type-Options: nosniff` is set
- [ ] `X-Frame-Options: DENY` is set
- [ ] `Referrer-Policy: no-referrer` is set
- [ ] File downloads set `Content-Disposition: attachment` and the correct MIME type
- [ ] API responses set `Content-Type: application/json`

## CORS

- [ ] `allow_origins` does not contain `"*"`
- [ ] Only `GET` and `POST` methods are allowed
- [ ] `allow_credentials` is `False`

## Rate Limiting

- [ ] nginx `limit_req_zone` is configured for upload (5r/m) and API (30r/m) endpoints
- [ ] FastAPI `slowapi` rate limiting is active as defense-in-depth
- [ ] Rate-limited responses return HTTP 429 with a JSON body

## Session and Temp Files

- [ ] Each session uses a unique UUID-named directory under `/app/tmp/`
- [ ] Background cleanup task removes session dirs older than 70 minutes
- [ ] On startup, all existing session directories are purged
- [ ] Files are never served cross-session (session ID validated on download)
- [ ] `umask 0077` is set so files are not world-readable

## Docker

- [ ] Container runs as non-root user (`USER appuser` in Dockerfile)
- [ ] Base image is `python:3.12-slim` or `python:3.12-alpine`, pinned by digest
- [ ] Root filesystem is read-only; `/app/tmp` is a tmpfs mount
- [ ] All capabilities are dropped (`cap_drop: ALL`)
- [ ] `no-new-privileges` security option is set
- [ ] Memory limit is set (2G max)
- [ ] `.dockerignore` excludes `.git`, `node_modules`, `__pycache__`, `.env`, test fixtures
- [ ] No secrets, credentials, or `.env` values baked into the image
- [ ] Multi-stage build: frontend built in Node stage, copied to final image

## Dependencies

- [ ] All Python packages are pinned to exact versions in `requirements.txt`
- [ ] `package-lock.json` is committed
- [ ] `pip-audit` passes with no high/critical findings **(CI)**
- [ ] `npm audit` passes with no high/critical findings **(CI)**
- [ ] `bandit` passes with no medium+ findings **(CI)**
- [ ] `hadolint` passes on Dockerfile **(CI)**
- [ ] `trivy` image scan passes with no high/critical CVEs **(CI)**

---

## Quick CLI Verification Commands

```bash
# Python security lint
bandit -r backend/ --severity-level medium

# Python dependency audit
pip-audit -r requirements.txt

# JS dependency audit
cd frontend && npm audit --audit-level=high

# Dockerfile lint
hadolint docker/Dockerfile

# Container image scan
trivy image --severity HIGH,CRITICAL xaf-converter:latest

# Verify response headers (with running instance)
curl -sI http://localhost/ | grep -E "Content-Security|X-Frame|X-Content-Type|Referrer-Policy"

# Verify CORS is not open
curl -sI -H "Origin: http://evil.com" http://localhost/api/ | grep -i "access-control"

# Check for XXE vulnerability (should be rejected or entity not resolved)
curl -X POST http://localhost/api/upload \
  -F "file=@tests/security/xxe_test.xaf" \
  | grep -v "root:"
```
