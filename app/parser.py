from bs4 import BeautifulSoup
from .normalize import clean, normalize_registration, normalize_phone, normalize_email

CAPTCHA_PHRASES = ("security code", "captcha", "verification", "case sensitive")

def detect_captcha(html: str) -> bool:
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True).lower()
    return any(p in text for p in CAPTCHA_PHRASES)

def discover_form(html: str):
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return None
    fields = []
    for tag in form.find_all(["input", "select", "textarea"]):
        name = tag.get("name")
        if not name:
            continue
        fields.append({"name": name, "type": tag.get("type", tag.name), "value": tag.get("value", "")})
    return {"action": form.get("action"), "method": (form.get("method") or "get").lower(), "fields": fields}

def parse_records(html: str, source_url: str):
    soup = BeautifulSoup(html, "html.parser")
    records = []
    # Flexible table parser: supports current directory-style tables and related public CoA lists.
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [clean(x.get_text(" ", strip=True)).lower() for x in rows[0].find_all(["th", "td"])]
        if not headers:
            continue
        for row in rows[1:]:
            cells = [clean(x.get_text(" ", strip=True)) for x in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            rec = dict(zip(headers, cells))
            name = next((rec[h] for h in headers if "name" in h), None)
            reg = next((rec[h] for h in headers if "registration" in h or "reg no" in h), None)
            city = next((rec[h] for h in headers if h == "city"), None)
            valid = next((rec[h] for h in headers if "valid" in h), None)
            if name or reg:
                records.append({
                    "architect_name": name,
                    "registration_number": normalize_registration(reg),
                    "city": city,
                    "valid_upto": valid,
                    "source_url": source_url,
                })
    return records
