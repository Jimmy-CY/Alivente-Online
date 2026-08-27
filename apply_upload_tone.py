"""apply_upload_tone - base.html learns one more icon action: upload.

    python apply_upload_tone.py --check
    python apply_upload_tone.py

base.html only. Two rules, and deliberately NO new colour.

WHY A CLASS AND NOT A COLOUR
----------------------------
base.html already carries six icon tones - edit blue, view teal, delete red,
approve green, unapprove amber, send teal. tenant_lease_agreement.html has a
seventh action, Upload, which it paints Bootstrap `#007bff` locally.

Three ways to give it a home, and only one of them is small:

  - reuse `.icon-edit`     -> the class name would say "edit" on a button
                              that uploads. The markup would be lying.
  - a new colour           -> a seventh tone every future page has to know
                              about, bought for one button on one screen.
  - a new CLASS on the OLD colour -> `.icon-upload` pointing at `--alv-edit`.

The third. Upload writes to the record, exactly as Edit does, and this page
already renders its mobile Upload in Bootstrap's blue - so blue is what the
button already is; this only puts it on the token and gives it an honest
name. The palette stays at six.

If a later screen needs Upload to be visually distinct from Edit, the change
is one line - point `.icon-upload` at a new token - and every page carrying
the class follows. That is the whole reason for naming it separately now.

Idempotent. Backs up to .bak_uploadtone.
"""

import io
import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the root')

raw = open(BASE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

MARKER = 'a new name on an existing colour, not a seventh colour'

ANCHOR = """      /* Approve / unapprove / send, used by Physical Invoices. */
"""

RULE = """      /* Upload - %s.
         Aliased to --alv-edit because uploading a document writes to the
         record in the same way editing it does, and the palette is already
         six tones deep. It gets its OWN class rather than borrowing
         .icon-edit so the markup does not claim a button edits when it
         uploads - and so that pointing it somewhere else later is one line
         here rather than a search across every page. */
      .icon-upload   { color: var(--alv-edit); border-color: #c9d8f7; }
      .icon-upload:hover { background: var(--alv-edit); border-color: var(--alv-edit); color: #fff; }

""" % MARKER

MOBILE_ANCHOR = """        .icon-color-delete { color: var(--alv-danger); }
"""
MOBILE_RULE = """        .icon-color-delete { color: var(--alv-danger); }
        .icon-color-upload { color: var(--alv-edit); }
"""

if MARKER in text:
    print('')
    print('  ALREADY  base.html already defines .icon-upload.')
    sys.exit(0)

for label, anchor in (('the icon-tone block', ANCHOR),
                      ('the mobile icon-colour block', MOBILE_ANCHOR)):
    n = text.count(anchor)
    if n != 1:
        sys.exit('! %s matched %d times, expected 1.\n'
                 '  base.html has changed since this was written - stopping '
                 'rather than guessing.' % (label, n))

text = text.replace(ANCHOR, RULE + ANCHOR, 1)
text = text.replace(MOBILE_ANCHOR, MOBILE_RULE, 1)

# ------------------------------------------------------- verify before write
problems = []
if text.count('.icon-upload ') + text.count('.icon-upload:') != 2:
    problems.append('expected exactly two .icon-upload rules')
if text.count('.icon-color-upload') != 1:
    problems.append('expected exactly one .icon-color-upload rule')
# The point of the whole exercise: no new colour entered the file.
_hexes_before = raw.decode(ENC).replace('\r\n', '\n')
import re as _re
_new = set(_re.findall(r'#[0-9a-fA-F]{6}\b', text)) - \
    set(_re.findall(r'#[0-9a-fA-F]{6}\b', _hexes_before))
if _new:
    problems.append('a new colour entered base.html: %s - this patch is '
                    'supposed to add a NAME, not a tone' % ', '.join(sorted(_new)))
if text.count('<style') != text.count('</style>'):
    problems.append('style tags no longer balance')
# .icon-upload must sit with the other tones, AFTER .icon-action-btn defines
# the shape - a tone before its base rule loses the border-color it sets.
if text.index('.icon-upload') < text.index('.icon-action-btn {'):
    problems.append('.icon-upload sits before .icon-action-btn defines the '
                    'shape, so its border-color would be overwritten')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
print('  OK      .icon-upload        -> var(--alv-edit)')
print('  OK      .icon-color-upload  -> var(--alv-edit)   (mobile bar)')
print('  OK      no new colour entered base.html')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = BASE + '.bak_uploadtone'
if not os.path.exists(bak):
    shutil.copy2(BASE, bak)
with io.open(BASE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/base.html  (backup: .bak_uploadtone)')
