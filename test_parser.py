"""Quick smoke-test for the CRS Excel parser. Run with: python test_parser.py"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from crs.services.parser import parse

TEMPLATE_PATH = r"C:\Users\demet\Downloads\CRS_Design_v3.xlsx"  # adjust if needed

r = parse(TEMPLATE_PATH)

print(f"valid:       {r.is_valid}")
print(f"accounts:    {len(r.accounts)}")
print(f"corrections: {len(r.corrections)}")
print(f"errors:      {len(r.errors)}")
print()

for acct in r.accounts:
    print(f"  {acct.sheet} row {acct.row_number}: {acct.account_number}  (CPs: {len(acct.controlling_persons)})")
print()

for c in r.corrections[:10]:
    print(f"CORRECTION {c.sheet} {c.col}{c.row} [{c.field}]  {c.original!r} -> {c.corrected!r}  ({c.reason})")
print()

for err in r.errors[:10]:
    print(f"ERROR {err.sheet} {err.col}{err.row} [{err.field}]  {err.value!r}  ({err.reason})")