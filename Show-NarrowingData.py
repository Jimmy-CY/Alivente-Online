# -*- coding: utf-8 -*-
"""Show-NarrowingData.py - the live rows behind the IN-1 and RC-1 filters.

    python Show-NarrowingData.py

Run from the repo root. READ-ONLY - it opens a database connection, reads,
and writes nothing.

WHY IT EXISTS

  Rounds IN-1 and RC-1 add a way to narrow two screens that have none:
  Invoice Customers, and Cash Receipts. Three of the design choices turn
  on numbers nobody has looked at, and guessing them is how a filter ends
  up being the wrong shape for the data it filters.

    1. HOW MANY ROWS. A live filter that narrows as you type is cheap and
       needs no round trip - but every row has to be ON THE PAGE for it
       to hide one, and neither screen paginates. At forty rows that is
       right. At four thousand it is a slow page and a server filter is
       the answer. The number decides, not taste.

    2. WHAT "MONTH" MEANS ON RECEIPTS. Demetri asked for a Month filter.
       A dropdown of the months that actually HAVE receipts is a better
       control than a date picker if there are a dozen of them, and a
       worse one if there are two hundred. This prints the span and the
       count.

    3. WHETHER THE TOTAL IS ALREADY WRONG. cash_receipt_list sums

           sum(r['amount'] for r in rows if not r['is_void'])

       across every row, and cash_receipts.html prints the answer with a
       hardcoded euro sign. CashReceipt HAS a `currency` column with a
       default of EUR. If a single receipt was ever issued in anything
       else, TOTAL ISSUED is adding unlike things together and has been
       doing it silently. That is not a filter question, but RC-1 is the
       round that touches the line, so it is the round that should know.

  Same habit as Show-ProjectRollup.py and Show-UserEmails.py: a question
  about live rows is answered from live rows, before the round is built.

WHAT IT DOES NOT DO

  It writes nothing, changes nothing, and prints no customer address or
  email - only counts, dates and currency codes.
"""
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
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django                                                    # noqa: E402
django.setup()                                                   # noqa: E402

from collections import Counter                                  # noqa: E402
from decimal import Decimal                                      # noqa: E402

# A TOOL THAT CAN RUN AGAINST TWO DATABASES MUST SAY WHICH ONE IT IS ON.
# The same line the rollup tools print, for the same reason: a production
# question was once answered from the development database twice. See
# pages/db_banner.py.
from pages.db_banner import print_banner                         # noqa: E402

BAR = '=' * 78

print(BAR)
print('Show-NarrowingData.py - the rows behind the IN-1 and RC-1 filters')
print(BAR)
print_banner()
print('')
print('READ-ONLY. Nothing is written. No address or email is printed.')
print('')

# THE CONNECTION IS THE FIRST THING THAT CAN FAIL, AND A TRACEBACK SAYS
# LESS ABOUT WHY THAN ONE SENTENCE DOES.
#
# `railway run` injects production's environment variables but runs
# Python ON THIS MACHINE. Railway's MYSQLHOST is a .railway.internal
# name, which resolves only inside Railway's own network - so from a
# laptop it fails in DNS before it ever reaches MySQL. That is not a
# fault in this tool and not a fault in the database.
try:
    from pages.models import CashReceipt, InvoiceCustomer
    n_customers = InvoiceCustomer.objects.count()
    receipts = list(CashReceipt.objects.all()
                    .values('receipt_date', 'currency', 'amount', 'is_void',
                            'payer_name'))
except Exception as e:
    from pages.db_banner import describe_database
    host = str(describe_database()['host'])
    print('')
    print(BAR)
    print('  COULD NOT REACH THE DATABASE')
    print(BAR)
    print('  %s' % str(e)[:150])
    print('')
    if host.endswith('.railway.internal'):
        print('  The host is %s' % host)
        print('')
        print('  That is Railway\'s PRIVATE name. It resolves only from')
        print('  inside Railway, so `railway run` cannot reach it from a')
        print('  laptop - railway run sets the variables here and runs the')
        print('  process here. Two ways round it:')
        print('')
        print('  1. RUN IT INSIDE RAILWAY (no password needed on your')
        print('     machine, and the private name resolves):')
        print('')
        print('         railway ssh')
        print('         python Show-NarrowingData.py')
        print('')
        print('     The file has to be in the deployed commit for this.')
        print('')
        print('  2. OR POINT AT THE PUBLIC PROXY from here, exactly as you')
        print('     did for Show-UserEmails.py - the same five variables,')
        print('     and WITHOUT railway run, which would put the private')
        print('     name back.')
    else:
        print('  Check that %s is reachable from here.' % host)
    print(BAR)
    raise SystemExit(1)

# ---- 1. Invoice Customers ------------------------------------------------
print(BAR)
print('IN-1  INVOICE CUSTOMERS')
print(BAR)
print('  %d customer(s) on the book.' % n_customers)
print('')
if n_customers <= 150:
    print('  Every row already renders - there is no pagination on that')
    print('  screen - so a LIVE filter that narrows as you type costs one')
    print('  search box and two attributes, and no round trip.')
else:
    print('  *** That is more than a page should render at once. A live')
    print('      filter hides rows that are already there, so at this size')
    print('      the page itself is the problem and the filter wants to')
    print('      run on the SERVER.')

# ---- 2. Cash Receipts ----------------------------------------------------
print('')
print(BAR)
print('RC-1  CASH RECEIPTS')
print(BAR)
n = len(receipts)
print('  %d receipt(s).' % n)
if not n:
    print('  Nothing issued yet - every question below is unanswerable from')
    print('  data, so the filter should be built for the shape you expect.')
    print(BAR)
    raise SystemExit(0)

voids = sum(1 for r in receipts if r['is_void'])
print('  %d issued, %d void.' % (n - voids, voids))
print('')

dates = sorted(r['receipt_date'] for r in receipts if r['receipt_date'])
months = sorted({(d.year, d.month) for d in dates})
print('  Earliest %s   latest %s' % (dates[0], dates[-1]))
print('  %d distinct month(s) have a receipt in them.' % len(months))
if len(months) <= 36:
    print('')
    print('  A DROPDOWN OF THE MONTHS THAT EXIST is the better control at')
    print('  this size: every option in it returns rows, which a date')
    print('  picker cannot promise. Months with a receipt:')
    for y, m in months:
        c = sum(1 for d in dates if (d.year, d.month) == (y, m))
        print('        %04d-%02d   %d' % (y, m, c))
else:
    print('')
    print('  Too many months for a dropdown. A From / To date pair is the')
    print('  control that scales.')

# ---- 3. the currency question -------------------------------------------
print('')
print(BAR)
print('THE TOTAL ISSUED LINE - IS IT ADDING UNLIKE THINGS?')
print(BAR)
codes = Counter((r['currency'] or '').strip().upper() or '(blank)'
                for r in receipts)
for code, count in sorted(codes.items()):
    print('  %-10s %d receipt(s)' % (code, count))
print('')
if len(codes) <= 1:
    only = list(codes)[0]
    print('  One currency only (%s), so the hardcoded euro sign on the' % only)
    print('  TOTAL ISSUED line and the blind sum behind it are both correct')
    print('  TODAY. They are correct by accident rather than by design - the')
    print('  column exists and nothing stops a second currency being used -')
    print('  but RC-1 does not have to fix it, and should say so rather')
    print('  than quietly leave it.')
else:
    print('  *** %d CURRENCIES. TOTAL ISSUED sums every row regardless and' % len(codes))
    print('      prints the answer with a hardcoded euro sign, so the number')
    print('      on that screen is adding unlike things together and has')
    print('      been doing it silently. Per currency, issued only:')
    per = {}
    for r in receipts:
        if r['is_void']:
            continue
        k = (r['currency'] or '').strip().upper() or '(blank)'
        per[k] = per.get(k, Decimal('0.00')) + (r['amount'] or Decimal('0.00'))
    for k in sorted(per):
        print('        %-10s %s' % (k, per[k]))
    print('')
    print('      RC-1 touches that line to make it follow the filter. It is')
    print('      the round that should decide what it says.')

# ---- 4. Received From ----------------------------------------------------
print('')
print(BAR)
print('THE "RECEIVED FROM" CONTROL')
print(BAR)
payers = Counter((r['payer_name'] or '').strip() for r in receipts)
payers.pop('', None)
print('  %d distinct payer name(s) across %d receipt(s).'
      % (len(payers), n))
print('')
if len(payers) <= 40:
    print('  Few enough for a DROPDOWN, which beats free text: it cannot be')
    print('  misspelt and it cannot return nothing. The names are')
    print('  snapshotted on the receipt, so the list is what was actually')
    print('  typed, not the tenant table.')
else:
    print('  Too many for a dropdown. Free text, matched case-insensitively')
    print('  on a contains, is the control that scales.')

print('')
print(BAR)
print('  Nothing was written. Run it again after any change and compare.')
print(BAR)
