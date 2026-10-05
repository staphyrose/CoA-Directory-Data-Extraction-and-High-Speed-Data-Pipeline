import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import init_db, connect
from app.normalize import normalize_registration, normalize_email, normalize_phone

ROOT=Path(__file__).resolve().parents[1]
init_db()
with connect() as c:
    count=c.execute("SELECT COUNT(*) FROM architects WHERE source_type='public_sample'").fetchone()[0]
    if count==0:
        path=ROOT/'data'/'coa_sample.csv'
        with path.open(encoding='utf-8') as f:
            for r in csv.DictReader(f):
                c.execute("""INSERT OR IGNORE INTO architects(architect_name,registration_number,city,valid_upto,source_url,source_type,record_scope,extracted_at,processing_status,duplicate_status) VALUES(?,?,?,?,?,?,?,?,?,?)""",(r['architect_name'],normalize_registration(r['registration_number']),r['city'],r['valid_upto'],r['source_url'],'public_sample','public_defaulters_list',r['extracted_at'],'success','unique'))
        c.commit()
print('Database ready.')
