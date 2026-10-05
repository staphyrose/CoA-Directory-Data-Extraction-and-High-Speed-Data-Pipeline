```python
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

import requests

from .config import *
from .db import connect
from .normalize import source_hash, clean, normalize_registration, normalize_phone
from .parser import detect_captcha, discover_form, parse_records


# ============================================================
# LOGGING
# ============================================================

# Make sure the logs directory exists before logging starts.
# This is important for cloud deployment platforms such as Render.
LOG_DIR = Path(LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# CoA EXTRACTOR
# ============================================================

class CoAExtractor:

    def __init__(self, delay=REQUEST_DELAY_SECONDS):
        self.delay = delay

        # Create a reusable HTTP session.
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT
        })

    # ========================================================
    # FETCH
    # ========================================================

    def fetch(self, url):
        """
        Fetch a URL with retry handling.

        Retries are performed for:
        - HTTP 429
        - HTTP 500
        - HTTP 502
        - HTTP 503
        - HTTP 504
        - Network/request errors

        Exponential backoff is used between attempts.
        """

        last = None

        for attempt in range(MAX_RETRIES):

            try:
                logger.info(
                    "Request attempt %s/%s: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    url
                )

                r = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT
                )

                # Handle temporary/server/rate-limit responses.
                if r.status_code in (429, 500, 502, 503, 504):

                    last = f"HTTP {r.status_code}"

                    logger.warning(
                        "Retryable HTTP response: %s",
                        r.status_code
                    )

                    time.sleep(
                        min(30, 2 ** attempt)
                    )

                    continue

                r.raise_for_status()

                logger.info(
                    "Successful response: HTTP %s",
                    r.status_code
                )

                return r

            except requests.RequestException as e:

                last = str(e)

                logger.warning(
                    "Request error: %s",
                    e
                )

                time.sleep(
                    min(30, 2 ** attempt)
                )

        raise RuntimeError(
            last or "request failed"
        )

    # ========================================================
    # CREATE JOB
    # ========================================================

    def create_job(self, category, query_value):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as c:

            cur = c.execute(
                """
                INSERT INTO extraction_jobs
                (
                    category,
                    query_value,
                    status,
                    started_at,
                    latest_activity
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    category,
                    query_value,
                    "running",
                    now,
                    now
                )
            )

            job_id = cur.lastrowid

        logger.info(
            "Created extraction job %s: category=%s query=%s",
            job_id,
            category,
            query_value
        )

        return job_id

    # ========================================================
    # EVENT
    # ========================================================

    def event(
        self,
        job_id,
        event_type,
        message,
        url=None,
        http_status=None
    ):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as c:

            c.execute(
                """
                INSERT INTO extraction_events
                (
                    job_id,
                    event_type,
                    message,
                    url,
                    http_status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    event_type,
                    message,
                    url,
                    http_status,
                    now
                )
            )

            c.execute(
                """
                UPDATE extraction_jobs
                SET latest_activity=?
                WHERE id=?
                """,
                (
                    now,
                    job_id
                )
            )

        logger.info(
            "Job %s event [%s]: %s",
            job_id,
            event_type,
            message
        )

    # ========================================================
    # SAVE RECORDS
    # ========================================================

    def save_records(
        self,
        job_id,
        records,
        source_type="directory",
        scope="live_directory"
    ):

        saved = 0
        dup = 0

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as c:

            for rec in records:

                reg = normalize_registration(
                    rec.get("registration_number")
                )

                try:

                    c.execute(
                        """
                        INSERT INTO architects
                        (
                            architect_name,
                            architecture_id,
                            registration_number,
                            registration_year,
                            address,
                            state,
                            city,
                            pincode,
                            phone,
                            email,
                            registration_status,
                            valid_upto,
                            source_url,
                            source_type,
                            record_scope,
                            extracted_at,
                            processing_status,
                            duplicate_status,
                            raw_hash
                        )
                        VALUES
                        (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            clean(
                                rec.get("architect_name")
                            ),

                            rec.get(
                                "architecture_id"
                            ),

                            reg,

                            rec.get(
                                "registration_year"
                            ),

                            clean(
                                rec.get("address")
                            ),

                            clean(
                                rec.get("state")
                            ),

                            clean(
                                rec.get("city")
                            ),

                            clean(
                                rec.get("pincode")
                            ),

                            normalize_phone(
                                rec.get("phone")
                            ),

                            rec.get("email"),

                            clean(
                                rec.get(
                                    "registration_status"
                                )
                            ),

                            clean(
                                rec.get("valid_upto")
                            ),

                            rec.get(
                                "source_url",
                                DIRECTORY_URL
                            ),

                            source_type,

                            scope,

                            now,

                            "success",

                            "unique",

                            rec.get("raw_hash")
                        )
                    )

                    saved += 1

                except Exception as e:

                    # Duplicate record
                    if "UNIQUE constraint failed" in str(e):

                        dup += 1

                        c.execute(
                            """
                            INSERT INTO extraction_events
                            (
                                job_id,
                                event_type,
                                message,
                                created_at
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                job_id,
                                "duplicate",
                                "Duplicate record skipped",
                                now
                            )
                        )

                        logger.info(
                            "Duplicate record skipped for job %s",
                            job_id
                        )

                    # Other record-level error
                    else:

                        c.execute(
                            """
                            INSERT INTO extraction_events
                            (
                                job_id,
                                event_type,
                                message,
                                created_at
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                job_id,
                                "record_error",
                                str(e),
                                now
                            )
                        )

                        logger.exception(
                            "Record error for job %s",
                            job_id
                        )

            # Update job counters.
            c.execute(
                """
                UPDATE extraction_jobs
                SET
                    success_count =
                        success_count + ?,
                    duplicate_count =
                        duplicate_count + ?
                WHERE id=?
                """,
                (
                    saved,
                    dup,
                    job_id
                )
            )

        logger.info(
            "Job %s saved=%s duplicates=%s",
            job_id,
            saved,
            dup
        )

        return saved, dup

    # ========================================================
    # RUN CATEGORY PAGE
    # ========================================================

    def run_category_page(
        self,
        category,
        query_value
    ):

        job = self.create_job(
            category,
            query_value
        )

        url = (
            f"{COA_BASE}"
            f"/search_arch2.php"
            f"?lang=1"
            f"&level=1"
            f"&linkid="
            f"&lid=289"
            f"&searCat={CATEGORIES[category]}"
        )

        try:

            # ------------------------------------------------
            # FETCH PAGE
            # ------------------------------------------------

            r = self.fetch(url)

            # ------------------------------------------------
            # STORE RAW RESPONSE
            # ------------------------------------------------

            with connect() as c:

                c.execute(
                    """
                    INSERT INTO raw_responses
                    (
                        job_id,
                        url,
                        response_hash,
                        status_code,
                        captured_at,
                        content
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job,
                        url,
                        source_hash(r.text),
                        r.status_code,
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                        r.text[:200000]
                    )
                )

            # ------------------------------------------------
            # CAPTCHA / SECURITY DETECTION
            # ------------------------------------------------

            if detect_captcha(r.text):

                message = (
                    "Security verification detected. "
                    "Manual completion required; "
                    "no bypass attempted."
                )

                self.event(
                    job,
                    "captcha_required",
                    message,
                    url,
                    r.status_code
                )

                with connect() as c:

                    c.execute(
                        """
                        UPDATE extraction_jobs
                        SET
                            status=?,
                            captcha_count =
                                captcha_count + 1
                        WHERE id=?
                        """,
                        (
                            "captcha_required",
                            job
                        )
                    )

                logger.warning(
                    "CAPTCHA/security verification detected "
                    "for job %s. Extraction paused.",
                    job
                )

                return {
                    "job_id": job,
                    "status": "captcha_required",
                    "form": discover_form(r.text)
                }

            # ------------------------------------------------
            # PARSE RECORDS
            # ------------------------------------------------

            records = parse_records(
                r.text,
                url
            )

            # ------------------------------------------------
            # SAVE RECORDS
            # ------------------------------------------------

            saved, dup = self.save_records(
                job,
                records
            )

            # ------------------------------------------------
            # COMPLETE JOB
            # ------------------------------------------------

            with connect() as c:

                c.execute(
                    """
                    UPDATE extraction_jobs
                    SET
                        status=?,
                        total_identified=?,
                        finished_at=?
                    WHERE id=?
                    """,
                    (
                        "completed",
                        len(records),
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                        job
                    )
                )

            logger.info(
                "Job %s completed successfully. "
                "Records=%s duplicates=%s",
                job,
                saved,
                dup
            )

            return {
                "job_id": job,
                "status": "completed",
                "records": saved,
                "duplicates": dup
            }

        # ----------------------------------------------------
        # ERROR HANDLING
        # ----------------------------------------------------

        except Exception as e:

            logger.exception(
                "Job %s failed",
                job
            )

            self.event(
                job,
                "http_error",
                str(e),
                url
            )

            with connect() as c:

                c.execute(
                    """
                    UPDATE extraction_jobs
                    SET
                        status=?,
                        error_info=?,
                        finished_at=?
                    WHERE id=?
                    """,
                    (
                        "failed",
                        str(e),
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                        job
                    )
                )

            return {
                "job_id": job,
                "status": "failed",
                "error": str(e)
            }
```

### Now do this

After replacing the file:

1. Save `extractor.py`.
2. Upload/commit the changed file to GitHub.
3. Go to **Render → your service → Events**.
4. Render should automatically start a new deployment.
5. Wait for **Live**.

The important fix is these two lines:

```python
LOG_DIR = Path(LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)
```

That ensures Render creates:

```text
logs/
└── pipeline.log
```

automatically instead of crashing with:

```text
FileNotFoundError: No such file or directory: '/opt/render/project/src/logs/pipeline.log'
```

Also, I noticed your original file uses `normalize_phone(...)` but the import line you pasted does **not** import it. I've corrected that too:

```python
from .normalize import source_hash, clean, normalize_registration, normalize_phone
```

So use the **whole file above**, not just the two-line fix.
