"""Quick smoke-test for the CRS Excel parser. Run with: python test_parser.py"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

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