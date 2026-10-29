#!/bin/sh
# HK-5, 29 Oct 2026 - RAILWAY DOES NOT RUN THIS FILE. The cron-service's
# Custom Start Command is a loop that calls check_lease_renewal_and_invoices
# at 06:00 UTC every day (his screenshot and the run log of 29 Oct). This
# file named check_lease_renewals, a command that does not exist, and began
# with a byte-order mark sh could not read - kept, corrected, so that
# running it by hand does what the daily job does.
set -e
cd /app
exec python manage.py check_lease_renewal_and_invoices
