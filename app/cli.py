import argparse
from .db import init_db
from .extractor import CoAExtractor

p=argparse.ArgumentParser(description="Respectful CoA directory extractor")
p.add_argument("--category", choices=["name","year","registration_number","state","city","pincode"], required=True)
p.add_argument("--value", required=True)
p.add_argument("--max-pages", type=int, default=1)
args=p.parse_args()
init_db()
print(CoAExtractor().run_category_page(args.category,args.value))
