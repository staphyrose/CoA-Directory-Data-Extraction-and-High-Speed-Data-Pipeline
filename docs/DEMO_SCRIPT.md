# 2-minute demonstration script

1. Run `run.bat` and open the dashboard.
2. Point out the sample public records, SQLite-backed counts, and CSV export.
3. Explain the six live CoA search categories.
4. Submit a live extraction query from the dashboard.
5. If the live site returns its security code page, show that the job becomes `captcha_required` rather than attempting a bypass.
6. Show `data/coa.db`, `data/schema.sql`, and `logs/pipeline.log`.
7. Run the unit tests with `python -m pytest` if pytest is installed, or execute the individual test file after installing pytest.
8. Explain that records are committed incrementally and duplicates are rejected by a database uniqueness constraint.
