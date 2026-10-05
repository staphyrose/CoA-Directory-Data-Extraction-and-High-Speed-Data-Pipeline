# Assignment Requirements Matrix

| Requirement | Implementation |
|---|---|
| Study complete workflow | docs/INVESTIGATION_NOTES.md |
| Search/retrieval/display investigation | docs/INVESTIGATION_NOTES.md; app/config.py; app/parser.py |
| Registration IDs | app/normalize.py; DB registration_number |
| All available fields | DB schema includes name, architecture_id, registration number/year, address, state, city, pincode, phone, email, status, valid_upto, source metadata |
| Public endpoint/data-access investigation | docs/INVESTIGATION_NOTES.md |
| Large-data pipeline | app/extractor.py |
| Batching/concurrency policy | extractor is designed for controlled sequential requests; delay is configurable to avoid overloading source |
| Avoid repeated requests | SQLite uniqueness + raw response hashes |
| Immediate storage | save_records commits in SQLite transactions |
| Indexes | registration, city, state, processing-status indexes |
| Pending/failed/completed | extraction_jobs + processing_status |
| Resume | persistent job and record state; successful records remain after interruption |
| Speed measurement | extraction_jobs.records_per_second field and dashboard statistics |
| CAPTCHA detection/pause/manual resume | app/parser.py + app/extractor.py |
| Rate limits/retries/backoff | app/extractor.py |
| HTTP error logging | extraction_events + logs/pipeline.log |
| Database repository | data/coa.db + data/schema.sql |
| Duplicate handling | UNIQUE constraint + duplicate events |
| Data quality | normalization utilities and nullable incomplete records |
| Progress dashboard | app/dashboard.py |
| Final dataset/statistics | data/coa_sample.csv and dashboard |
| Complete source | app/, scripts/, tests/ |
| Documentation | README + docs/ |
| Demonstration-ready | dashboard starts with sample records |
