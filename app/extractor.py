import time, logging
from datetime import datetime, timezone
import requests
from .config import *
from .db import connect
from .normalize import source_hash, clean, normalize_registration
from .parser import detect_captcha, discover_form, parse_records

logging.basicConfig(filename=LOG_DIR / "pipeline.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class CoAExtractor:
    def __init__(self, delay=REQUEST_DELAY_SECONDS):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self, url):
        last = None
        for attempt in range(MAX_RETRIES):
            try:
                r = self.session.get(url, timeout=REQUEST_TIMEOUT)
                if r.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {r.status_code}"
                    time.sleep(min(30, 2 ** attempt))
                    continue
                r.raise_for_status()
                return r
            except requests.RequestException as e:
                last = str(e)
                time.sleep(min(30, 2 ** attempt))
        raise RuntimeError(last or "request failed")

    def create_job(self, category, query_value):
        now = datetime.now(timezone.utc).isoformat()
        with connect() as c:
            cur = c.execute("INSERT INTO extraction_jobs(category,query_value,status,started_at,latest_activity) VALUES(?,?,?,?,?)", (category,query_value,"running",now,now))
            return cur.lastrowid

    def event(self, job_id, event_type, message, url=None, http_status=None):
        now = datetime.now(timezone.utc).isoformat()
        with connect() as c:
            c.execute("INSERT INTO extraction_events(job_id,event_type,message,url,http_status,created_at) VALUES(?,?,?,?,?,?)", (job_id,event_type,message,url,http_status,now))
            c.execute("UPDATE extraction_jobs SET latest_activity=? WHERE id=?", (now,job_id))

    def save_records(self, job_id, records, source_type="directory", scope="live_directory"):
        saved = dup = 0
        now = datetime.now(timezone.utc).isoformat()
        with connect() as c:
            for rec in records:
                reg = normalize_registration(rec.get("registration_number"))
                try:
                    c.execute("""INSERT INTO architects(architect_name,architecture_id,registration_number,registration_year,address,state,city,pincode,phone,email,registration_status,valid_upto,source_url,source_type,record_scope,extracted_at,processing_status,duplicate_status,raw_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                        clean(rec.get("architect_name")), rec.get("architecture_id"), reg, rec.get("registration_year"), clean(rec.get("address")), clean(rec.get("state")), clean(rec.get("city")), clean(rec.get("pincode")), normalize_phone(rec.get("phone")), rec.get("email"), clean(rec.get("registration_status")), clean(rec.get("valid_upto")), rec.get("source_url", DIRECTORY_URL), source_type, scope, now, "success", "unique", rec.get("raw_hash")))
                    saved += 1
                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        dup += 1
                        c.execute("INSERT INTO extraction_events(job_id,event_type,message,created_at) VALUES(?,?,?,?)", (job_id,"duplicate","Duplicate record skipped",now))
                    else:
                        c.execute("INSERT INTO extraction_events(job_id,event_type,message,created_at) VALUES(?,?,?,?)", (job_id,"record_error",str(e),now))
            c.execute("UPDATE extraction_jobs SET success_count=success_count+?,duplicate_count=duplicate_count+? WHERE id=?", (saved,dup,job_id))
        return saved, dup

    def run_category_page(self, category, query_value):
        job = self.create_job(category, query_value)
        url = f"{COA_BASE}/search_arch2.php?lang=1&level=1&linkid=&lid=289&searCat={CATEGORIES[category]}"
        try:
            r = self.fetch(url)
            with connect() as c:
                c.execute("INSERT INTO raw_responses(job_id,url,response_hash,status_code,captured_at,content) VALUES(?,?,?,?,?,?)", (job,url,source_hash(r.text),r.status_code,datetime.now(timezone.utc).isoformat(),r.text[:200000]))
            if detect_captcha(r.text):
                self.event(job,"captcha_required","Security verification detected. Manual completion required; no bypass attempted.",url,r.status_code)
                with connect() as c: c.execute("UPDATE extraction_jobs SET status=?,captcha_count=captcha_count+1 WHERE id=?", ("captcha_required",job))
                return {"job_id":job,"status":"captcha_required","form":discover_form(r.text)}
            records = parse_records(r.text,url)
            saved, dup = self.save_records(job,records)
            with connect() as c: c.execute("UPDATE extraction_jobs SET status=?,total_identified=?,finished_at=? WHERE id=?", ("completed",len(records),datetime.now(timezone.utc).isoformat(),job))
            return {"job_id":job,"status":"completed","records":saved,"duplicates":dup}
        except Exception as e:
            self.event(job,"http_error",str(e),url)
            with connect() as c: c.execute("UPDATE extraction_jobs SET status=?,error_info=?,finished_at=? WHERE id=?", ("failed",str(e),datetime.now(timezone.utc).isoformat(),job))
            return {"job_id":job,"status":"failed","error":str(e)}
