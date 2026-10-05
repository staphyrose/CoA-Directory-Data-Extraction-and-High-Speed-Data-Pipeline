import re
from hashlib import sha256

def clean(value):
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value)).strip()
    return s or None

def normalize_email(value):
    v = clean(value)
    return v.lower() if v else None

def normalize_phone(value):
    v = clean(value)
    if not v:
        return None
    return re.sub(r"[^0-9+]", "", v)

def normalize_registration(value):
    v = clean(value)
    return v.upper().replace(" ", "") if v else None

def source_hash(text):
    return sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()

def record_key(record):
    return normalize_registration(record.get("registration_number")) or clean(record.get("architect_name"))
