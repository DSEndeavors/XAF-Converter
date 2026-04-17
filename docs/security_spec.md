# XAF Converter Security Specification

## 1. Project Profile

| Attribute | Value |
|---|---|
| Application | Web-based XAF-to-export converter |
| Stack | FastAPI (Python) backend, React frontend, nginx reverse proxy |
| Deployment | Single Docker container, self-hosted |
| Authentication | None (open access on the host network) |
| Data sensitivity | Financial / tax audit data (XAF 4.0) |
| File size ceiling | 250 MB per upload |
| Session lifetime | 1 hour or manual restart |

Because there is **no authentication**, every defence must assume the caller is untrusted.

---

## 2. Threat Model

### 2.1 Assets to Protect

| Asset | Impact if compromised |
|---|---|
| Host filesystem | Full server compromise |
| Other users' session data | Data leak of financial records |
| Container runtime | Escape to host, lateral movement |
| Backend process | Denial of service, code execution |
| Exported files served to users | Data poisoning, formula injection |

### 2.2 Threat Actors

| Actor | Motivation |
|---|---|
| Curious user on same network | Access other sessions' data |
| Automated scanner / bot | Exploit known vulnerabilities |
| Malicious file submitter | RCE, data exfiltration, DoS |

### 2.3 Attack Surface

```
Internet/LAN
    │
    ▼
  nginx (reverse proxy, static files)
    │
    ▼
  FastAPI (uvicorn)
    ├── POST /upload  ← file upload endpoint
    ├── GET  /export  ← file download endpoint
    ├── POST /restart ← session reset
    └── internal: XML parsing, export generation
    │
    ▼
  Temp filesystem (session-scoped directories)
```

---

## 3. Security Requirements

### 3.1 XXE Prevention (CRITICAL)

XAF files are XML. XML External Entity attacks are the **number one risk**.

**Requirements:**

- R-XXE-1: **Never use `lxml.etree.parse()` or `xml.etree.ElementTree` with default settings.** Always use `defusedxml` as the primary XML parser.
- R-XXE-2: Install and import `defusedxml`. Use `defusedxml.ElementTree.parse()` or `defusedxml.lxml.parse()` for all XML parsing.
- R-XXE-3: If `lxml` is needed for XPath or schema validation, create the parser with all dangerous features disabled:
  ```python
  from lxml import etree
  parser = etree.XMLParser(
      resolve_entities=False,
      no_network=True,
      dtd_validation=False,
      load_dtd=False,
      huge_tree=False,   # prevents billion-laughs DoS
  )
  ```
- R-XXE-4: **Never** enable `resolve_entities`, `load_dtd`, or `no_network=False`.
- R-XXE-5: Add an integration test that submits an XML file containing `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>` and verifies it is rejected or the entity is not resolved.
- R-XXE-6: Add an integration test for a billion-laughs payload (exponential entity expansion) and verify it is rejected or limited.

**Packages:**
- `defusedxml>=0.7.1` (mandatory)
- `lxml` (optional, only if needed; always configure parser as above)

---

### 3.2 File Upload Security

**Requirements:**

- R-UP-1: Reject any upload where `Content-Length` exceeds 250 MB. Enforce this in **both** nginx (`client_max_body_size 250m;`) and FastAPI (check `request.headers["content-length"]` before reading body).
- R-UP-2: After receiving the file, verify the first bytes are a valid XML declaration (`<?xml`) or a BOM followed by `<?xml`. Reject otherwise.
- R-UP-3: Restrict accepted filename extensions to `.xaf` and `.xml` (case-insensitive). Reject all others.
- R-UP-4: **Never** use the client-supplied filename for storage. Generate a UUID-based filename:
  ```python
  import uuid
  safe_name = f"{uuid.uuid4()}.xaf"
  ```
- R-UP-5: Enforce a maximum XML nesting depth of 100 levels during parsing. Use iterative parsing with depth tracking or `lxml`'s `huge_tree=False`.
- R-UP-6: Set a parsing timeout of 60 seconds. If parsing has not completed, kill the task and return HTTP 422.
- R-UP-7: Limit total disk usage per session to 500 MB (upload + generated exports). Check before writing.

---

### 3.3 Path Traversal Prevention

**Requirements:**

- R-PT-1: All temporary files must be stored under a single configurable base directory (e.g., `/app/tmp`).
- R-PT-2: Session directories must be created as subdirectories of the base: `/app/tmp/{session_id}/`.
- R-PT-3: **Every** file path operation must call a validation function that resolves the path and confirms it starts with the base directory:
  ```python
  import os

  TEMP_BASE = "/app/tmp"

  def safe_path(base: str, *parts: str) -> str:
      joined = os.path.join(base, *parts)
      resolved = os.path.realpath(joined)
      if not resolved.startswith(os.path.realpath(base) + os.sep):
          raise ValueError(f"Path traversal attempt: {joined}")
      return resolved
  ```
- R-PT-4: Never pass user-supplied strings (filenames, session IDs) directly into `os.path.join`, `open()`, or `pathlib.Path()` without validation through the `safe_path` function.
- R-PT-5: Session IDs must be validated as UUID format (`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`) before use in any path construction.

---

### 3.4 Export Injection Prevention

Crafted XAF field values could exploit export formats (CSV formula injection, XLSX macro injection, JSON injection).

**Requirements:**

- R-EX-1: **CSV formula injection**: Prefix any cell value starting with `=`, `+`, `-`, `@`, `\t`, `\r`, or `\n` with a single quote (`'`). Alternatively, wrap all values in explicit quoting with `quoting=csv.QUOTE_ALL`.
- R-EX-2: **XLSX**: Use `openpyxl` with `write_only=True` mode. Never embed macros. Set cell types explicitly to `string` for all text fields. Numeric fields must be validated as numbers before writing as numeric type.
- R-EX-3: **JSON**: Use `json.dumps()` with `ensure_ascii=True` to prevent Unicode-based injection. Validate that no field value exceeds 10,000 characters.
- R-EX-4: **Parquet**: Use `pyarrow` with explicit schema definitions. Never infer schema from data. All string columns must be typed as `pa.string()`, numeric as `pa.float64()` or `pa.int64()`.
- R-EX-5: Sanitize all string values extracted from the XAF by stripping null bytes (`\x00`) and other control characters (U+0000-U+001F except `\n`, `\t`).
- R-EX-6: Truncate individual field values at 50,000 characters to prevent memory exhaustion.

---

### 3.5 Docker Hardening

**Requirements:**

- R-DK-1: Use a minimal base image: `python:3.12-slim` or `python:3.12-alpine`.
- R-DK-2: Create and run as a non-root user:
  ```dockerfile
  RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
  USER appuser
  ```
- R-DK-3: Make the application filesystem read-only. Mount `/app/tmp` as a tmpfs volume:
  ```yaml
  # docker-compose.yml
  read_only: true
  tmpfs:
    - /app/tmp:size=1G,mode=1777
    - /tmp:size=100M
  ```
- R-DK-4: Drop all Linux capabilities and add back only what is needed:
  ```yaml
  cap_drop:
    - ALL
  security_opt:
    - no-new-privileges:true
  ```
- R-DK-5: Set resource limits:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
  ```
- R-DK-6: No `.env` files, secrets, or credentials should be baked into the image. Verify with:
  ```bash
  docker history --no-trunc <image> | grep -i -E "env|secret|password|key"
  ```
- R-DK-7: Use a `.dockerignore` that excludes `.git`, `node_modules`, `__pycache__`, `.env`, `*.pyc`, and test fixtures.
- R-DK-8: Pin all base image versions by digest, not just tag.
- R-DK-9: Run a multi-stage build: build frontend in a Node stage, copy static files to the final Python stage.

---

### 3.6 Dependency Security

**Requirements:**

- R-DEP-1: Pin all Python dependencies in `requirements.txt` with exact versions (e.g., `fastapi==0.115.0`).
- R-DEP-2: Pin all npm dependencies with a lockfile (`package-lock.json`); commit it.
- R-DEP-3: Run `pip-audit` in CI on every PR:
  ```bash
  pip install pip-audit
  pip-audit -r requirements.txt
  ```
- R-DEP-4: Run `npm audit` in CI on every PR.
- R-DEP-5: Use `safety` as a second-opinion vulnerability scanner:
  ```bash
  pip install safety
  safety check -r requirements.txt
  ```
- R-DEP-6: Review and update dependencies monthly. Document the review date in a `DEPENDENCY_REVIEW.md` or a comment in `requirements.txt`.
- R-DEP-7: Never use `pip install` without version pins in the Dockerfile.

---

### 3.7 CORS Policy

**Requirements:**

- R-CORS-1: In FastAPI, configure CORS middleware to allow only same-origin:
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[],        # No cross-origin requests
      allow_credentials=False,
      allow_methods=["GET", "POST"],
      allow_headers=["Content-Type"],
  )
  ```
- R-CORS-2: Since the frontend is served by nginx from the same origin, the API needs **no** cross-origin allowances. If `allow_origins=["*"]` ever appears in the codebase, treat it as a security bug.
- R-CORS-3: In nginx, add:
  ```nginx
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-Frame-Options "DENY" always;
  ```

---

### 3.8 Content Security Policy (CSP) and Response Headers

**Requirements:**

- R-CSP-1: nginx must set the following headers on all responses:
  ```nginx
  add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self';" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-Frame-Options "DENY" always;
  add_header Referrer-Policy "no-referrer" always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
  ```
- R-CSP-2: If the React build uses inline scripts (e.g., Vite injects `<script type="module">`), use a nonce-based CSP or hash-based CSP instead of `'unsafe-inline'` for `script-src`. **Never** set `script-src 'unsafe-inline'`.
- R-CSP-3: FastAPI API responses must include `Content-Type: application/json` explicitly. File downloads must set the correct MIME type and `Content-Disposition: attachment`.

---

### 3.9 Rate Limiting

**Requirements:**

- R-RL-1: Apply rate limiting at the nginx level:
  ```nginx
  limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/m;
  limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

  location /api/upload {
      limit_req zone=upload burst=2 nodelay;
      proxy_pass http://backend;
  }

  location /api/ {
      limit_req zone=api burst=10 nodelay;
      proxy_pass http://backend;
  }
  ```
- R-RL-2: Upload endpoint: max 5 requests per minute per IP.
- R-RL-3: General API endpoints: max 30 requests per minute per IP.
- R-RL-4: Return HTTP 429 with a JSON body `{"detail": "Too many requests"}` when rate-limited.
- R-RL-5: As defense-in-depth, also apply rate limiting in FastAPI using `slowapi`:
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @app.post("/api/upload")
  @limiter.limit("5/minute")
  async def upload(request: Request, file: UploadFile):
      ...
  ```

---

### 3.10 Temp File Cleanup and Session Isolation

**Requirements:**

- R-TMP-1: Each session gets a unique directory: `/app/tmp/{session_uuid}/`.
- R-TMP-2: On session expiry (1 hour) or manual restart, delete the entire session directory recursively:
  ```python
  import shutil
  shutil.rmtree(session_dir, ignore_errors=False)
  ```
- R-TMP-3: Run a background cleanup task every 10 minutes that removes any session directory older than 70 minutes (grace period of 10 min beyond the 1-hour expiry).
- R-TMP-4: On application startup, purge all existing session directories in `/app/tmp/`.
- R-TMP-5: Never serve files from one session to a request associated with a different session. Validate the session ID in the request against the file's parent directory.
- R-TMP-6: Set `umask 0077` (or `os.umask(0o077)`) so that temp files are only readable by the application user.
- R-TMP-7: Use `tempfile.mkdtemp(dir=TEMP_BASE)` as an alternative to manual directory creation, to ensure atomic creation without race conditions.

---

## 4. Security Scanning Tools

### 4.1 Static Analysis (Python)

| Tool | Purpose | Command |
|---|---|---|
| `bandit` | Python security linter | `bandit -r backend/ -f json` |
| `semgrep` | Pattern-based vulnerability scanner | `semgrep --config=p/python --config=p/owasp-top-ten backend/` |
| `ruff` | Fast linter with security rules | `ruff check backend/ --select S` (S = bandit rules) |

### 4.2 Dependency Scanning

| Tool | Purpose | Command |
|---|---|---|
| `pip-audit` | Python CVE scanner | `pip-audit -r requirements.txt` |
| `safety` | Python CVE scanner (second opinion) | `safety check -r requirements.txt` |
| `npm audit` | JS CVE scanner | `cd frontend && npm audit` |

### 4.3 Container Scanning

| Tool | Purpose | Command |
|---|---|---|
| `trivy` | Container image CVE scanner | `trivy image xaf-converter:latest` |
| `hadolint` | Dockerfile linter | `hadolint docker/Dockerfile` |
| `dockle` | Container best-practice checker | `dockle xaf-converter:latest` |

### 4.4 Runtime / Dynamic

| Tool | Purpose | Notes |
|---|---|---|
| `nikto` | Web server scanner | Run against deployed instance |
| `curl`-based smoke tests | Verify headers (CSP, CORS, etc.) | Automate in CI |

---

## 5. CI/CD Integration

Every pull request must pass these gates before merge:

1. `bandit -r backend/ --severity-level medium` exits 0
2. `pip-audit -r requirements.txt` exits 0
3. `npm audit --audit-level=high` exits 0
4. `hadolint docker/Dockerfile` exits 0
5. All XXE and path-traversal integration tests pass
6. `trivy image --exit-code 1 --severity HIGH,CRITICAL xaf-converter:latest` exits 0

---

## 6. Incident Response Notes

Since this app has no authentication and handles financial data:

- If a vulnerability is discovered in production, immediately stop the container (`docker stop`).
- Purge all temp files: `rm -rf /app/tmp/*`.
- Review nginx access logs for signs of exploitation.
- Rebuild the container from a known-good commit after patching.
- Notify any users who may have had sessions active during the exposure window.
