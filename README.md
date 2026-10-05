# CoA Directory Data Extraction & High-Speed Data Pipeline

Technical examination submission for the Council of Architecture (CoA) public architect directory.

## What is included
- Investigation notes documenting the public website workflow and constraints.
- A production-style, resumable extraction pipeline with SQLite persistence.
- HTML parser that discovers forms/fields rather than hard-coding only one response shape.
- CAPTCHA/security-verification detection with safe manual-pause/resume handling.
- Rate limiting, retries with exponential backoff, HTTP error logging, duplicate detection and validation.
- Dashboard showing totals, pending/success/failed/duplicate counts, speed, start/latest activity and CAPTCHA events.
- CSV export and SQLite database/schema export.
- Real public CoA sample records available at submission time for immediate demonstration.
- Automated tests for normalization, duplicate handling and parser behavior.

## Quick start (Windows)
1. Install Python 3.10+.
2. Open this folder in Command Prompt/PowerShell.
3. Run `run.bat`.
4. Open http://127.0.0.1:5000

The dashboard starts with the included sample database, so it is demonstrable without making requests to CoA.

## Live extraction
The CoA directory currently presents category search pages such as Search by Name, Year of Registration, Registration Number, State, City and Pincode. The current live search pages require a case-sensitive security code. The extractor therefore opens the relevant search page, detects the challenge, records a CAPTCHA event and pauses for the operator. It never attempts to solve or bypass the security control.

From the dashboard, use **Prepare live extraction** to create a pending job. For a permitted manual workflow, the operator can open the CoA URL in a browser, complete the security verification themselves, then resume/record the resulting HTML through the supplied import workflow.

## Command-line extraction
Example:
`python -m app.cli --category registration_number --value CA/2023/154496 --max-pages 1`

If the source requests verification, the run exits safely with status `captcha_required` and leaves all prior records committed.

## Database
SQLite database: `data/coa.db`

Main tables:
- `architects`
- `extraction_jobs`
- `extraction_events`
- `raw_responses`

The schema is also exported to `data/schema.sql`.

## Data provenance
`data/coa_sample.csv` contains publicly displayed CoA records from the public CoA list available at submission time. Those rows are intentionally identified with `source_type=public_sample` and `record_scope=public_defaulters_list`; they are not represented as a full directory extraction. The live-directory extractor is separate and respects the site's verification/access controls.

## Assignment coverage
See `docs/REQUIREMENTS_MATRIX.md` for a requirement-by-requirement mapping to implementation files.

## Public deployment (Render)
This project is deployment-ready for a Python web service such as Render.

- Build command: `pip install -r requirements.txt`
- Start command: `python scripts/bootstrap.py && gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app.dashboard:app`
- Health check: `/`

After deployment, Render provides a public HTTPS URL such as `https://coa-directory-data-extraction.onrender.com`.

Note: the included SQLite database is suitable for demonstration. On hosts with ephemeral storage, local SQLite changes may be lost after a service restart/redeploy. The included public sample data is automatically bootstrapped when needed.
