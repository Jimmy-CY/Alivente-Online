#!/usr/bin/env python
"""
install_indicators_mobile_polish.py  --  stack the Financial Indicators controls
full-width on mobile (matches the app's responsive standard).

The year/basis row and the trend controls (Indicator, Years, Compare) previously
only wrapped on small screens. This adds a @media (max-width:768px) rule so they
stack full-width and stay easy to tap, consistent with how the rest of the app
handles control rows on mobile. The 16px iOS-zoom input guard was already present
and applies to these selects.

Edits one file (backup finance/financial_indicators.html.bak_fimobile):
  * pages/templates/finance/financial_indicators.html : classes on the trend header
    + controls, and a mobile stacking style block.

SAFE: idempotent; exact-anchor; preserves CRLF/LF; checks template tag balance;
--dry-run. No migration. Requires the trend + year-range installers applied.

    python install_indicators_mobile_polish.py --dry-run
    python install_indicators_mobile_polish.py
Then restart / redeploy.
"""
import base64, os, re, sys
DRY = '--dry-run' in sys.argv

# ---- payloads (base64, machine-generated) ----
H_OLD = (
    "ICAgIDxkaXYgaWQ9ImZpVHJlbmRTZWN0aW9uIiBzdHlsZT0ibWFyZ2luLXRvcDozMHB4OyI+CiAgICAgICAgPGRpdiBzdHlsZT0i"
    "ZGlzcGxheTpmbGV4OyBhbGlnbi1pdGVtczpjZW50ZXI7IGp1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuOyBmbGV4LXdyYXA6"
    "d3JhcDsgZ2FwOjEycHg7IG1hcmdpbi1ib3R0b206MTBweDsiPg=="
)
H_NEW = (
    "ICAgIDxkaXYgaWQ9ImZpVHJlbmRTZWN0aW9uIiBzdHlsZT0ibWFyZ2luLXRvcDozMHB4OyI+CiAgICAgICAgPGRpdiBjbGFzcz0i"
    "ZmktdHJlbmQtaGVhZGVyIiBzdHlsZT0iZGlzcGxheTpmbGV4OyBhbGlnbi1pdGVtczpjZW50ZXI7IGp1c3RpZnktY29udGVudDpz"
    "cGFjZS1iZXR3ZWVuOyBmbGV4LXdyYXA6d3JhcDsgZ2FwOjEycHg7IG1hcmdpbi1ib3R0b206MTBweDsiPg=="
)
C_OLD = (
    "ICAgICAgICAgICAgPGRpdiBzdHlsZT0iZGlzcGxheTpmbGV4OyBnYXA6MTBweDsgYWxpZ24taXRlbXM6Y2VudGVyOyBmbGV4LXdy"
    "YXA6d3JhcDsiPgogICAgICAgICAgICAgICAgPGxhYmVsIGZvcj0iZmlUcmVuZEluZGljYXRvciIgc3R5bGU9ImZvbnQtd2VpZ2h0"
    "OjYwMDsgbWFyZ2luOjA7Ij5JbmRpY2F0b3I8L2xhYmVsPg=="
)
C_NEW = (
    "ICAgICAgICAgICAgPGRpdiBjbGFzcz0iZmktdHJlbmQtY29udHJvbHMiIHN0eWxlPSJkaXNwbGF5OmZsZXg7IGdhcDoxMHB4OyBh"
    "bGlnbi1pdGVtczpjZW50ZXI7IGZsZXgtd3JhcDp3cmFwOyI+CiAgICAgICAgICAgICAgICA8bGFiZWwgZm9yPSJmaVRyZW5kSW5k"
    "aWNhdG9yIiBzdHlsZT0iZm9udC13ZWlnaHQ6NjAwOyBtYXJnaW46MDsiPkluZGljYXRvcjwvbGFiZWw+"
)
S_OLD = (
    "ICAgIDwhLS0gWWVhciArIEJhc2lzIGNvbnRyb2xzICh5ZWFyLWF3YXJlIEZpbmFuY2lhbCBJbmRpY2F0b3JzKSAtLT4KICAgIDxk"
    "aXYgY2xhc3M9ImZpLWNvbnRyb2xzIg=="
)
S_NEW = (
    "ICAgIDxzdHlsZT4KICAgIC8qIE1vYmlsZTogc3RhY2sgdGhlIEZpbmFuY2lhbCBJbmRpY2F0b3JzIGNvbnRyb2xzIGZ1bGwtd2lk"
    "dGggKG1hdGNoZXMgYXBwIHN0YW5kYXJkKSAqLwogICAgQG1lZGlhIChtYXgtd2lkdGg6IDc2OHB4KSB7CiAgICAgICAgLmZpLWNv"
    "bnRyb2xzIHsgZmxleC1kaXJlY3Rpb246IGNvbHVtbiAhaW1wb3J0YW50OyBhbGlnbi1pdGVtczogc3RyZXRjaCAhaW1wb3J0YW50"
    "OyB9CiAgICAgICAgLmZpLWNvbnRyb2xzID4gZGl2IHsgd2lkdGg6IDEwMCU7IH0KICAgICAgICAuZmktY29udHJvbHMgc2VsZWN0"
    "IHsgd2lkdGg6IDEwMCUgIWltcG9ydGFudDsgfQogICAgICAgIC5maS10cmVuZC1oZWFkZXIgeyBmbGV4LWRpcmVjdGlvbjogY29s"
    "dW1uICFpbXBvcnRhbnQ7IGFsaWduLWl0ZW1zOiBzdHJldGNoICFpbXBvcnRhbnQ7IH0KICAgICAgICAuZmktdHJlbmQtY29udHJv"
    "bHMgeyBmbGV4LWRpcmVjdGlvbjogY29sdW1uICFpbXBvcnRhbnQ7IGFsaWduLWl0ZW1zOiBzdHJldGNoICFpbXBvcnRhbnQ7IH0K"
    "ICAgICAgICAuZmktdHJlbmQtY29udHJvbHMgc2VsZWN0LAogICAgICAgIC5maS10cmVuZC1jb250cm9scyAjZmlDb21wYXJlV3Jh"
    "cCwKICAgICAgICAuZmktdHJlbmQtY29udHJvbHMgI2ZpQ29tcGFyZUJ0biB7IHdpZHRoOiAxMDAlICFpbXBvcnRhbnQ7IH0KICAg"
    "ICAgICAuZmktdHJlbmQtY29udHJvbHMgI2ZpQ29tcGFyZVBhbmVsIHsgd2lkdGg6IDEwMCU7IG1pbi13aWR0aDogMDsgfQogICAg"
    "fQogICAgPC9zdHlsZT4KCiAgICA8IS0tIFllYXIgKyBCYXNpcyBjb250cm9scyAoeWVhci1hd2FyZSBGaW5hbmNpYWwgSW5kaWNh"
    "dG9ycykgLS0+CiAgICA8ZGl2IGNsYXNzPSJmaS1jb250cm9scyI="
)

MARK = 'fi-trend-controls'

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p, 'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p, s, nl):
    with open(p, 'w', encoding='utf-8', newline=nl) as f: f.write(s)
def b64(s): return base64.b64decode(s).decode()

def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root.'); sys.exit(1)
    tpl = os.path.join(root, 'pages', 'templates', 'finance', 'financial_indicators.html')
    if not os.path.exists(tpl):
        print('!! financial_indicators.html not found.'); sys.exit(1)
    t = read(tpl)
    if 'fiTrendSection' not in t or 'fi-controls' not in t:
        print('!! Financial Indicators trend/controls not detected. Apply the trend installers first.'); sys.exit(1)
    print('financial_indicators.html:', tpl + ('   (dry run)' if DRY else '')); print('')
    if MARK in t:
        print('[skip] mobile polish already installed.'); print(''); return
    work = t
    for ob, nb in [(H_OLD, H_NEW), (C_OLD, C_NEW), (S_OLD, S_NEW)]:
        o, n = b64(ob), b64(nb)
        if work.count(o) != 1:
            print('!! template anchor not matched (found %d).' % work.count(o)); sys.exit(1)
        work = work.replace(o, n, 1)
    if len(re.findall(r'{%\s*if\b', work)) != len(re.findall(r'{%\s*endif\s*%}', work)):
        print('!! template tag balance broke. Nothing changed.'); sys.exit(1)
    if DRY:
        print('[dry-run] would add mobile stacking for the FI controls.'); print(''); return
    nl = detect_nl(tpl); b = tpl + '.bak_fimobile'
    if not os.path.exists(b): write(b, t, nl)
    write(tpl, work, nl); print('[OK] financial_indicators.html updated (.bak_fimobile).')
    print(''); print('Mobile polish installed. Restart / redeploy; controls stack full-width on phones.')

if __name__ == '__main__': main()