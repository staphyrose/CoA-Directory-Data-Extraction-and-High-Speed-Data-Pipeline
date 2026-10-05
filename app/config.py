from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "coa.db"
LOG_DIR = ROOT / "logs"
COA_BASE = "https://coa.gov.in"
DIRECTORY_URL = COA_BASE + "/search_arch.php?lang=1&level=1&linkid=&lid=289&lang=1"
CATEGORIES = {
    "name": 1,
    "year": 2,
    "registration_number": 3,
    "state": 4,
    "city": 5,
    "pincode": 6,
}
REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2.0
MAX_RETRIES = 4
USER_AGENT = "CoA-Directory-Data-Pipeline/1.0 (educational examination; respectful pacing)"
