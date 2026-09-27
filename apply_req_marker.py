# -*- coding: utf-8 -*-
"""SECTION H, ROUND H1 - TWO DEAD BUTTONS ON PASSPORT/DOCUMENT MANAGEMENT

Found in testing, 27 Sep: on passport_management, "Add New Passport/ID" does
nothing when pressed, and so does the Edit pencil in the Actions column.

BOTH ARE THE SAME TWO LINES.

    function addNewDocument() {
        ...
        document.querySelector('#file_upload_group .required-marker')
                .style.display = 'inline';      <- THROWS
        $('#addEditModal').modal('show');        <- never reached
    }

    function editDocument(...) {
        ...
        document.querySelector('#file_upload_group .required-marker')
                .style.display = 'none';        <- THROWS
        $('#addEditModal').modal('show');        <- never reached
    }

The markup inside #file_upload_group now reads

    <span class="alv-req">*</span>

An earlier round renamed the required marker to base's own .alv-req in the
MARKUP and left the SCRIPT asking for the old name. querySelector returns
null, `.style` raises TypeError, and the function dies ONE STATEMENT BEFORE
it would open the modal - so the button silently does nothing.

Rendered and confirmed in Chromium before this fix was written:

    querySelector('#file_upload_group .required-marker')  ->  null
    ... .style.display = 'inline'   ->  TypeError: Cannot read properties
                                        of null (reading 'style')
    querySelector('#file_upload_group .alv-req')          ->  <span
                                        class="alv-req">*</span>
    ... .style.display = 'inline'   ->  no error

THIS IS LESSON 50, LIVE: "a class name lives in three places - CSS, markup
and SCRIPT." It was already written down. The rename honoured two of the
three.

THE WHOLE TREE WAS SCANNED for the same fault - an UNGUARDED dereference,
`querySelector(X).something`, where X appears nowhere in the markup and is
not built by the script itself. Across 134 templates there are exactly two
hits, and the second is a false positive: physical_invoice_edit asks for
`#pi-suggest-data`, which Django's `{{ … |json_script:"pi-suggest-data" }}`
emits at render time, and it is inside a try/catch besides. So this is the
only one.

Backups: .bak_reqmarker. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_reqmarker'
CRLF = {}

REL = 'passport_management.html'
OLD = "document.querySelector('#file_upload_group .required-marker')"
NEW = "document.querySelector('#file_upload_group .alv-req')"
# What the markup really provides, asserted before the swap so a third
# rename stops this round instead of pointing the script at nothing again.
MARKUP = '<span class="alv-req">*</span>'
HOLDER = 'id="file_upload_group"'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def patch():
    path = os.path.join(ROOT, REL)
    if not os.path.isfile(path):
        raise SystemExit('H1: %s is not on disk' % REL)
    text = read(path)

    if OLD not in text and text.count(NEW) == 2:
        return 0                                  # already applied

    # --- the target must really be there, or the fix is another guess ----
    if HOLDER not in text:
        raise SystemExit('H1: %s - there is no #file_upload_group' % REL)
    i = text.index(HOLDER)
    j = text.find('</div>', i)
    if MARKUP not in text[i:j + 6]:
        raise SystemExit('H1: %s - #file_upload_group does not contain %s - '
                         'the marker has been renamed again, and pointing '
                         'the script at .alv-req would repeat the bug'
                         % (REL, MARKUP))

    n = text.count(OLD)
    if n != 2:
        raise SystemExit('H1: %s - expected 2 broken selectors, found %d'
                         % (REL, n))
    text = text.replace(OLD, NEW)

    # --- self-checks BEFORE anything is written -------------------------
    if 'required-marker' in text:
        raise SystemExit('H1: %s - a .required-marker reference survived'
                         % REL)
    if text.count(NEW) != 2:
        raise SystemExit('H1: %s - the new selector is present %d times'
                         % (REL, text.count(NEW)))
    for fn in ('addNewDocument', 'editDocument'):
        m = re.search(r'function\s+%s\s*\([^)]*\)\s*\{' % fn, text)
        if not m:
            raise SystemExit('H1: %s - %s is gone' % (REL, fn))
        k, d = m.end(), 1
        while d and k < len(text):
            d += 1 if text[k] == '{' else (-1 if text[k] == '}' else 0)
            k += 1
        body = text[m.start():k]
        if NEW not in body:
            raise SystemExit('H1: %s - %s no longer asks for the marker'
                             % (REL, fn))
        if "modal('show')" not in body:
            raise SystemExit('H1: %s - %s no longer opens the modal'
                             % (REL, fn))
    before = read(path)
    if len(text) != len(before) - n * len('required-marker') \
            + n * len('alv-req'):
        raise SystemExit('H1: %s - more changed than the two selectors' % REL)

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return n


LATER = [
    ('alv_rounds.py',
     "    '.bak_bartop',\n]",
     "    '.bak_bartop',\n    '.bak_reqmarker',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_bar_top.py'",
     "    'test_bar_top.py'\n    'test_req_marker.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('H1/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION H, ROUND H1 - TWO DEAD BUTTONS ON PASSPORT MANAGEMENT - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    n = patch()
    later = patch_later()
    print('  %-42s %s' % (REL, '%d selector(s) repointed to .alv-req' % n
                          if n else 'already applied'))
    print('-' * 74)
    print('  Add New Passport/ID and the Edit pencil both open their modal '
          'again.')
    print('  %d LATER edit(s).' % later)
    print('=' * 74)


if __name__ == '__main__':
    main()
