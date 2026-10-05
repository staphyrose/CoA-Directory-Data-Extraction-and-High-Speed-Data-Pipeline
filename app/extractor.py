import time
import logging
from pathlib import Path
from datetime import datetime, timezone

import requests

from .config import *
from .db import connect
from .normalize import (
    source_hash,
    clean,
    normalize_registration,
    normalize_phone,
)
from .parser import (
    detect_captcha,
    discover_form,
    parse_records,
)


# ============================================================
# LOGGING
# ============================================================

# Ensure the logs directory exists before Python creates
# the pipeline log file. This is required for cloud hosting
# platforms such as Render.
LOG_DIR = Path(LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# CoA EXTRACTOR
# ============================================================

class CoAExtractor:

    def __init__(self, delay=REQUEST_DELAY_SECONDS):
        self.delay = delay

        # Reusable HTTP session
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT
        })

    # ========================================================
    # FETCH
    # ========================================================

    def fetch(self, url):
        """
        Fetch a URL with retry and exponential backoff.

        Retryable HTTP statuses:
        429, 500, 502, 503, 504
        """

        last_error = None

        for attempt in range(MAX_RETRIES):

            try:

                logger.info(
                    "Request attempt %s/%s: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    url,
                )

                response = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                )

                # Handle rate limiting and temporary
                # server-side errors.
                if response.status_code in (
                    429,
                    500,
                    502,
                    503,
                    504,
                ):

                    last_error = (
                        f"HTTP {response.status_code}"
                    )

                    logger.warning(
                        "Retryable HTTP response: %s",
                        response.status_code,
                    )

                    time.sleep(
                        min(30, 2 ** attempt)
                    )

                    continue

                response.raise_for_status()

                logger.info(
                    "Successful response: HTTP %s",
                    response.status_code,
                )

                return response

            except requests.RequestException as error:

                last_error = str(error)

                logger.warning(
                    "Request error: %s",
                    error,
                )

                time.sleep(
                    min(30, 2 ** attempt)
                )

        raise RuntimeError(
            last_error or "Request failed"
        )

    # ========================================================
    # CREATE EXTRACTION JOB
    # ========================================================

    def create_job(self, category, query_value):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as connection:

            cursor = connection.execute(
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
                    now,
                ),
            )

            job_id = cursor.lastrowid

        logger.info(
            "Created extraction job %s",
            job_id,
        )

        return job_id

    # ========================================================
    # RECORD EXTRACTION EVENT
    # ========================================================

    def event(
        self,
        job_id,
        event_type,
        message,
        url=None,
        http_status=None,
    ):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as connection:

            connection.execute(
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
                    now,
                ),
            )

            connection.execute(
                """
                UPDATE extraction_jobs
                SET latest_activity=?
                WHERE id=?
                """,
                (
                    now,
                    job_id,
                ),
            )

        logger.info(
            "Job %s | %s | %s",
            job_id,
            event_type,
            message,
        )

    # ========================================================
    # SAVE RECORDS
    # ========================================================

    def save_records(
        self,
        job_id,
        records,
        source_type="directory",
        scope="live_directory",
    ):

        saved = 0
        duplicates = 0

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with connect() as connection:

            for record in records:

                registration_number = (
                    normalize_registration(
                        record.get(
                            "registration_number"
                        )
                    )
                )

                try:

                    connection.execute(
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
                                record.get(
                                    "architect_name"
                                )
                            ),

                            record.get(
                                "architecture_id"
                            ),

                            registration_number,

                            record.get(
                                "registration_year"
                            ),

                            clean(
                                record.get(
                                    "address"
                                )
                            ),

                            clean(
                                record.get(
                                    "state"
                                )
                            ),

                            clean(
                                record.get(
                                    "city"
                                )
                            ),

                            clean(
                                record.get(
                                    "pincode"
                                )
                            ),

                            normalize_phone(
                                record.get(
                                    "phone"
                                )
                            ),

                            record.get(
                                "email"
                            ),

                            clean(
                                record.get(
                                    "registration_status"
                                )
                            ),

                            clean(
                                record.get(
                                    "valid_upto"
                                )
                            ),

                            record.get(
                                "source_url",
                                DIRECTORY_URL,
                            ),

                            source_type,

                            scope,

                            now,

                            "success",

                            "unique",

                            record.get(
                                "raw_hash"
                            ),
                        ),
                    )

                    saved += 1

                except Exception as error:

                    # Duplicate record
                    if (
                        "UNIQUE constraint failed"
                        in str(error)
                    ):

                        duplicates += 1

                        connection.execute(
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
                                now,
                            ),
                        )

                        logger.info(
                            "Duplicate record skipped "
                            "for job %s",
                            job_id,
                        )

                    # Other record-level error
                    else:

                        connection.execute(
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
                                str(error),
                                now,
                            ),
                        )

                        logger.exception(
                            "Record error for job %s",
                            job_id,
                        )

            # Update counters
            connection.execute(
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
                    duplicates,
                    job_id,
                ),
            )

        logger.info(
            "Job %s completed record save: "
            "saved=%s duplicates=%s",
            job_id,
            saved,
            duplicates,
        )

        return saved, duplicates

    # ========================================================
    # RUN CATEGORY PAGE
    # ========================================================

    def run_category_page(
        self,
        category,
        query_value,
    ):

        job_id = self.create_job(
            category,
            query_value,
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
            # FETCH
            # ------------------------------------------------

            response = self.fetch(url)

            # ------------------------------------------------
            # STORE RAW RESPONSE
            # ------------------------------------------------

            with connect() as connection:

                connection.execute(
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
                        job_id,
                        url,
                        source_hash(
                            response.text
                        ),
                        response.status_code,
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                        response.text[
                            :200000
                        ],
                    ),
                )

            # ------------------------------------------------
            # CAPTCHA / SECURITY DETECTION
            # ------------------------------------------------

            if detect_captcha(
                response.text
            ):

                message = (
                    "Security verification detected. "
                    "Manual completion required; "
                    "no bypass attempted."
                )

                self.event(
                    job_id,
                    "captcha_required",
                    message,
                    url,
                    response.status_code,
                )

                with connect() as connection:

                    connection.execute(
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
                            job_id,
                        ),
                    )

                logger.warning(
                    "Security verification detected "
                    "for job %s. Extraction paused.",
                    job_id,
                )

                return {
                    "job_id": job_id,
                    "status": "captcha_required",
                    "form": discover_form(
                        response.text
                    ),
                }

            # ------------------------------------------------
            # PARSE RECORDS
            # ------------------------------------------------

            records = parse_records(
                response.text,
                url,
            )

            # ------------------------------------------------
            # SAVE RECORDS
            # ------------------------------------------------

            saved, duplicates = (
                self.save_records(
                    job_id,
                    records,
                )
            )

            # ------------------------------------------------
            # COMPLETE JOB
            # ------------------------------------------------

            finished_at = datetime.now(
                timezone.utc
            ).isoformat()

            with connect() as connection:

                connection.execute(
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
                        finished_at,
                        job_id,
                    ),
                )

            logger.info(
                "Job %s completed successfully. "
                "Records=%s duplicates=%s",
                job_id,
                saved,
                duplicates,
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "records": saved,
                "duplicates": duplicates,
            }

        # ----------------------------------------------------
        # ERROR HANDLING
        # ----------------------------------------------------

        except Exception as error:

            logger.exception(
                "Job %s failed",
                job_id,
            )

            self.event(
                job_id,
                "http_error",
                str(error),
                url,
            )

            finished_at = datetime.now(
                timezone.utc
            ).isoformat()

            with connect() as connection:

                connection.execute(
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
                        str(error),
                        finished_at,
                        job_id,
                    ),
                )

            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(error),
            }
