"""apply_accent_shades - finish the job eca9db8 started.

    python apply_accent_shades.py --check
    python apply_accent_shades.py

THE BUG
-------
eca9db8 replaced #17a2b8 with #0e7c8b everywhere and its suite passed with
"no #17a2b8 left anywhere". That was true, and still insufficient.

Bootstrap 4.1.3's `info` family is THREE colours, not one:

    #17a2b8   at rest        <- swept
    #138496   :hover         <- MISSED, different hex
    #117a8b   :active/border  <- MISSED, different hex

Pages carry their own copies of the hover rule, and a page's <style> sits
LATER in the document than the base.html override, so the page wins. Measured
in Chromium, on the real files:

    .btn-info at rest   rgb(14, 124, 139)   #0e7c8b   correct
    .btn-info on hover  rgb(19, 132, 150)   #138496   the OLD teal

Every teal button in the system reverts to the old colour under the cursor.
So does the sidebar: base.html itself carries #138496 on
.sidebar-link.active:hover and .sidebar-toggle:hover, which is every page.

The lesson from last round was "an override above the framework loses". This
is the same lesson pointing the other way: an override in base.html loses to a
page that redeclares the same selector later. Neither is a cascade failure -
both are the cascade working exactly as specified, against an incomplete edit.

THE FIX
-------
Both darker shades collapse to ONE colour: #0a5e6a, already defined in
base.html as --alv-accent-ink and already documented there as "hover /
pressed". That is precisely what these are.

Two shades becoming one is deliberate. #138496 (fill) and #117a8b (border)
differed by three points of lightness - a distinction no one has ever seen.
The standard has one hover ink, so these become it.

WHY A LITERAL AND NOT var(--alv-accent-ink)
-------------------------------------------
Some occurrences are in JavaScript, not CSS - act_expense.html sets a Chart.js
borderColor. var() does not resolve in a JS string. The literal is correct in
both places; new code should use the token.

CONTRAST
--------
    #138496 on white   4.40:1
    #117a8b on white   5.02:1
    #0a5e6a on white   7.44:1
A hover state that is darker than its rest state is also the conventional
direction, which #138496 (LIGHTER than #0e7c8b's 4.91:1) was not.

Idempotent. Backs up every file it touches to .bak_shades.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

NEW_HEX = '0a5e6a'
NEW_RGB = (10, 94, 106)

# hex -> what it was in Bootstrap, for the report
OLD = {
    '138496': 'info :hover',
    '117a8b': 'info :active / border',
}
OLD_RGB = {
    (19, 132, 150): '138496',
    (17, 122, 139): '117a8b',
}

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the project root')

# The accent round must have happened, or this is patching a colour scheme
# that does not exist yet.
_base = open(BASE, encoding='utf-8-sig').read()
if '--alv-accent-ink:' not in _base:
    sys.exit('! --alv-accent-ink is not defined in base.html.\n'
             '  This round depends on the accent block from eca9db8.')
if '#' + NEW_HEX not in _base:
    sys.exit('! base.html does not define #%s.\n'
             '  Expected it as the value of --alv-accent-ink.' % NEW_HEX)

SEARCH_DIRS = [
    os.path.join(ROOT, 'pages', 'templates'),
    os.path.join(ROOT, 'pages', 'help_content'),
    os.path.join(ROOT, 'static'),
]

_hex_res = {h: re.compile('#' + h, re.I) for h in OLD}
_rgb_res = {rgb: re.compile(r'rgba?\(\s*%d\s*,\s*%d\s*,\s*%d\s*' % rgb, re.I)
            for rgb in OLD_RGB}


def targets():
    seen = []
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames if x != 'staticfiles']
            for f in sorted(filenames):
                if '.bak_' in f or not f.endswith(('.html', '.css', '.js')):
                    continue
                seen.append(os.path.join(dirpath, f))
    return seen


def sniff(path):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        return (raw[3:].decode('utf-8'), 'utf-8-sig',
                '\r\n' if b'\r\n' in raw else '\n')
    return raw.decode('utf-8'), 'utf-8', ('\r\n' if b'\r\n' in raw else '\n')


def write(path, text, enc, nl):
    bak = path + '.bak_shades'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with io.open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl != '\n' else text)


def sweep(text):
    counts = {}
    for h, rx in _hex_res.items():
        n = len(rx.findall(text))
        if n:
            counts[h] = n
            text = rx.sub('#' + NEW_HEX, text)
    for rgb, h in OLD_RGB.items():
        rx = _rgb_res[rgb]
        n = len(rx.findall(text))
        if n:
            counts[h + ' (rgb)'] = n

            def _sub(m):
                return re.sub(r'\d+\s*,\s*\d+\s*,\s*\d+',
                              '%d, %d, %d' % NEW_RGB, m.group(0), count=1)
            text = rx.sub(_sub, text)
    return text, counts


files = targets()
pending, report = {}, []
grand = {}

for path in files:
    text, enc, nl = sniff(path)
    text = text.replace('\r\n', '\n')
    new, counts = sweep(text)
    if counts:
        report.append((os.path.relpath(path, ROOT), counts))
        for k, v in counts.items():
            grand[k] = grand.get(k, 0) + v
    if new != text:
        pending[path] = (new, enc, nl)

print('')
if report:
    print('  %-46s %9s %9s' % ('FILE', '#138496', '#117a8b'))
    print('  ' + '-' * 68)
    for rel, c in sorted(report, key=lambda t: -sum(t[1].values())):
        a = c.get('138496', 0) + c.get('138496 (rgb)', 0)
        b = c.get('117a8b', 0) + c.get('117a8b (rgb)', 0)
        print('  %-46s %9d %9d' % (rel[:46], a, b))
    print('  ' + '-' * 68)
for h, why in OLD.items():
    print('  #%s  (%-22s) -> #%s   %d found'
          % (h, why, NEW_HEX, grand.get(h, 0) + grand.get(h + ' (rgb)', 0)))
print('')
print('  %d file(s) scanned, %d to change' % (len(files), len(pending)))

# base.html carries two of these on the sidebar, which is every page. Say so
# explicitly - it is the difference between "some buttons" and "the whole app".
_b = sniff(BASE)[0]
_sidebar = sum(len(rx.findall(_b)) for rx in _hex_res.values())
print('  base.html itself: %d occurrence(s)%s'
      % (_sidebar, '  <- the sidebar, on every page' if _sidebar else ''))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

if not pending:
    print('Nothing to do - already applied.')
    sys.exit(0)

for path, (text, enc, nl) in pending.items():
    write(path, text, enc, nl)
print('  wrote %d file(s). Backups: *.bak_shades' % len(pending))
print('')
print('Now run:  python test_accent_shades.py')
