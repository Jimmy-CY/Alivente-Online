#!/usr/bin/env python
"""
install_indicators_trend_axisgrace.py  --  give the trend chart Y-axis some
headroom so markers at the extremes aren't clipped by the axis line.

Adds Chart.js 'grace: 10%' to the trend y-axis, so the axis extends ~10% below the
lowest point and above the highest (e.g. a 0% cost year gets a little room below 0
instead of the dot sitting on the x-axis). Works for every indicator proportionally
(percentages and Rent €/m²). Client-side only.

Edits one file (backup finance/financial_indicators.html.bak_figrace):
  * pages/templates/finance/financial_indicators.html : the trend y-axis config.

SAFE: idempotent; exact-anchor; preserves CRLF/LF; --dry-run. No migration.
(Requires Chart.js 3.4+ for 'grace'; your build uses v3.)

    python install_indicators_trend_axisgrace.py --dry-run
    python install_indicators_trend_axisgrace.py
Then restart / redeploy.
"""
import base64, os, sys
DRY = '--dry-run' in sys.argv

OLD_B64 = "ICAgICAgICAgICAgICAgIHNjYWxlczogeyB5OiB7IHRpY2tzOiB7IGNhbGxiYWNrOiBmdW5jdGlvbiAodikgeyByZXR1cm4gKGluZCA9PT0gJ3JlbnRQZXJTcW0nID8gdi50b0ZpeGVkKDIpIDogdi50b0ZpeGVkKDEpKSArIHVuaXQoaW5kKTsgfSB9IH0gfQ=="
NEW_B64 = "ICAgICAgICAgICAgICAgIHNjYWxlczogeyB5OiB7IGdyYWNlOiAnMTAlJywgdGlja3M6IHsgY2FsbGJhY2s6IGZ1bmN0aW9uICh2KSB7IHJldHVybiAoaW5kID09PSAncmVudFBlclNxbScgPyB2LnRvRml4ZWQoMikgOiB2LnRvRml4ZWQoMSkpICsgdW5pdChpbmQpOyB9IH0gfSB9"

MARK = "grace: '10%'"

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p, 'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p, s, nl):
    with open(p, 'w', encoding='utf-8', newline=nl) as f: f.write(s)

def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root.'); sys.exit(1)
    tpl = os.path.join(root, 'pages', 'templates', 'finance', 'financial_indicators.html')
    if not os.path.exists(tpl):
        print('!! financial_indicators.html not found.'); sys.exit(1)
    t = read(tpl)
    if 'fiTrendChart' not in t:
        print('!! trend chart not detected. Apply the trend installers first.'); sys.exit(1)
    print('financial_indicators.html:', tpl + ('   (dry run)' if DRY else '')); print('')
    if MARK in t:
        print('[skip] axis grace already applied.'); print(''); return
    old, new = base64.b64decode(OLD_B64).decode(), base64.b64decode(NEW_B64).decode()
    if t.count(old) != 1:
        print('!! anchor not matched (found %d).' % t.count(old)); sys.exit(1)
    work = t.replace(old, new, 1)
    if DRY:
        print('[dry-run] would add 10%% grace to the trend y-axis.'); print(''); return
    nl = detect_nl(tpl); b = tpl + '.bak_figrace'
    if not os.path.exists(b): write(b, t, nl)
    write(tpl, work, nl); print('[OK] financial_indicators.html updated (.bak_figrace).')
    print(''); print('Axis grace added. Restart / redeploy; markers at the top/bottom now have room.')

if __name__ == '__main__': main()