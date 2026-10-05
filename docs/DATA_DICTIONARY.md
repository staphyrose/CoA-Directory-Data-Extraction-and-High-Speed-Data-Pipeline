# Data Dictionary

- `architect_name`: publicly displayed architect name.
- `architecture_id`: architecture/record ID when available.
- `registration_number`: normalized CoA registration number.
- `registration_year`: extracted registration year where available.
- `address`: address where publicly displayed.
- `state`, `city`, `pincode`: normalized location fields where available.
- `phone`, `email`: public contact fields where the source exposes them.
- `registration_status`: status where available.
- `valid_upto`: validity date where a public list exposes it.
- `source_url`: traceability URL.
- `source_type`: `directory` for live directory extraction; `public_sample` for included demonstration records.
- `record_scope`: describes the source scope.
- `extracted_at`: UTC extraction timestamp.
- `processing_status`: success/failed/pending.
- `duplicate_status`: unique/duplicate.
- `error_info`: error details without silently dropping incomplete rows.
- `raw_hash`: SHA-256 of captured response/source content when available.
