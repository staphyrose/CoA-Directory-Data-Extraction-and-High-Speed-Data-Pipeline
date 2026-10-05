import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.parser import detect_captcha, parse_records
from app.normalize import normalize_registration, normalize_phone

def test_captcha():
    assert detect_captcha('<html>Please Enter The Security Code shown in the Text Box Provided.</html>')

def test_registration_normalization():
    assert normalize_registration(' ca/2023/154496 ') == 'CA/2023/154496'

def test_phone_normalization():
    assert normalize_phone('+91 98765-43210') == '+919876543210'

def test_table_parser():
    html='''<table><tr><th>Sl.</th><th>Name</th><th>Registration Number</th><th>City</th><th>Valid up to</th></tr><tr><td>1</td><td>Ms. Test</td><td>CA/2023/1</td><td>Mumbai</td><td>31/12/2026</td></tr></table>'''
    rows=parse_records(html,'https://example.test')
    assert rows[0]['architect_name']=='Ms. Test'
    assert rows[0]['registration_number']=='CA/2023/1'
