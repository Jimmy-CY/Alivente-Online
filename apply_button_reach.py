"""apply_button_reach - the same four tones, everywhere a button lives.

    python apply_button_reach.py --check
    python apply_button_reach.py

Run AFTER apply_action_standard.py.

WHY
---
The action-bar round scoped its tones to the bar:
`.page-action-buttons .action-primary`. That was too narrow. Measured after
it shipped:

    modal footers ....... 32 buttons across 9 templates
                          confirm = btn-success x5, btn-info x3,
                          btn-primary x1, btn-danger x2; Cancel = grey x9
    Back outside a bar .. 19 templates, 4 of them via .back-button

So green means "confirm" in a modal while it also means "Active" on the
pill scale, and Back is teal-filled on four report pages and quiet on
nineteen others.

THE FIX IS STRUCTURAL, NOT COSMETIC
-----------------------------------
Split what the bar round conflated:

    LAYOUT  stays scoped to .page-action-buttons - sizing, the flex row,
            and the whole mobile collapse. That is bar behaviour and it
            has no business in a modal footer.
    TONE    goes unscoped. .action-primary / -secondary / -danger / -back
            set COLOUR ONLY, so they work in a bar, a modal footer, a
            report header or a card - and Bootstrap's .btn / .btn-sm keeps
            supplying the sizing wherever we are not the layout owner.

Colour-only also means `btn-sm` still works. The first draft of the bar
round set padding on the tone classes, which would have inflated the small
"quick add" buttons inside the Add Asset modal.

PRINTING
--------
The print block styled tables, cards and pills and never told the CHROME to
go away, so Property Assets printed its Add Asset button, its Back arrow and
its Group-by toggle. Interactive furniture does not belong on paper.

The hidden list names a few page-specific classes (.view-toggle-row,
.filter-panel). Impure, and right: they are the furniture that exists, and a
page cannot add itself to a base.html print rule.

Idempotent. Backs up each file to .bak_btnreach.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

MODALS = ('asset_detail.html', 'property_assets.html', 'suppliers.html')
BACKS = ('property_report.html', 'supplier_report.html',
         'lease_renewal_report.html', 'tenant_payment_days.html')
FILES = (('base.html',) + MODALS + BACKS
         + ('suppliers_edit.html', 'edit_asset.html'))

src, meta = {}, {}
for name in FILES:
    p = os.path.join(TPL, name)
    if not os.path.exists(p):
        sys.exit('! pages/templates/%s not found - run from the project root'
                 % name)
    raw = open(p, 'rb').read()
    meta[name] = ('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8',
                  '\r\n' if b'\r\n' in raw else '\n')
    src[name] = raw.decode(meta[name][0]).replace('\r\n', '\n')

if '--alv-actions-std' not in src['base.html']:
    sys.exit('! base.html has no action bar - apply_action_standard.py first.')

CHANGES = []


def sub(name, label, old, new, mark):
    done = mark(src[name]) if callable(mark) else (mark in src[name])
    if done:
        CHANGES.append((name, 'skip', label))
        return
    n = src[name].count(old)
    if n != 1:
        sys.exit('! %s / %s: the anchor matched %d times (expected 1)\n'
                 '  anchor: %s' % (name, label, n, old.strip()[:90]))
    src[name] = src[name].replace(old, new, 1)
    CHANGES.append((name, 'apply', label))


def subn(name, label, old, new, mark, count):
    done = mark(src[name]) if callable(mark) else (mark in src[name])
    if done:
        CHANGES.append((name, 'skip', label))
        return
    n = src[name].count(old)
    if n != count:
        sys.exit('! %s / %s: the anchor matched %d times (expected %d)\n'
                 '  anchor: %s' % (name, label, n, count, old.strip()[:90]))
    src[name] = src[name].replace(old, new)
    CHANGES.append((name, 'apply', '%s (x%d)' % (label, count)))


# =====================================================================
# 0.  repair a half-applied run
# =====================================================================
# The first version of this round unscoped the tones WITHOUT pairing them
# with .btn, which shipped and turned Help and Back solid teal on every page
# that has its own .btn-info. The corrected version below expects the
# ORIGINAL bar-scoped selectors as its anchor - so on a tree that already ran
# the buggy version, the anchor is gone and the patcher aborts having done
# nothing. That is exactly what happened.
#
# So: repair first. If the bare unscoped form is present, add the .btn.
# twin to it. Idempotent, and a no-op on a tree that never ran the bad one.
B = 'base.html'

_repairs = 0
if '.btn.action-primary' not in src[B]:
    for _tone in ('action-primary', 'action-secondary', 'action-danger'):
        _new, _k = re.subn(
            r'\n      \.%s \{' % _tone,
            '\n      .%s,\n      .btn.%s {' % (_tone, _tone), src[B])
        src[B] = _new
        _repairs += _k
        _new, _k = re.subn(
            r'\n      \.%s:hover,\n      \.%s:focus \{' % (_tone, _tone),
            '\n      .%s:hover,\n      .%s:focus,\n      .btn.%s:hover,'
            '\n      .btn.%s:focus {' % (_tone, _tone, _tone, _tone), src[B])
        src[B] = _new
        _repairs += _k
    _new, _k = re.subn(
        r'\n      \.action-back,\n      \.back-button \{',
        '\n      .action-back,\n      .back-button,\n      .btn.action-back,'
        '\n      .btn.back-button {', src[B])
    src[B] = _new
    _repairs += _k
    _new, _k = re.subn(
        r'\n      \.action-back:hover,\n      \.action-back:focus,'
        r'\n      \.back-button:hover,\n      \.back-button:focus \{',
        '\n      .action-back:hover,\n      .action-back:focus,'
        '\n      .back-button:hover,\n      .back-button:focus,'
        '\n      .btn.action-back:hover,\n      .btn.back-button:hover {',
        src[B])
    src[B] = _new
    _repairs += _k
if _repairs:
    CHANGES.append((B, 'apply',
                    'REPAIR: paired %d unscoped tone rules with .btn, so a '
                    "page's own .btn-info no longer beats them" % _repairs))


# =====================================================================
# 1.  base.html - split layout from tone
# =====================================================================

# The sizing rule keeps its scope: it IS bar layout.
sub(B, 'the tones stop being bar-only, and set colour ONLY',
    """      .page-action-buttons .action-primary {
        background: var(--alv-accent);
        border-color: var(--alv-accent);
        color: var(--alv-on-accent);
      }
      .page-action-buttons .action-primary:hover,
      .page-action-buttons .action-primary:focus {
        background: var(--alv-accent-ink);
        border-color: var(--alv-accent-ink);
        color: var(--alv-on-accent);
        text-decoration: none;
      }

      .page-action-buttons .action-secondary {
        background: var(--alv-paper);
        border-color: var(--alv-line);
        color: var(--alv-ink);
      }
      .page-action-buttons .action-secondary:hover,
      .page-action-buttons .action-secondary:focus {
        background: var(--alv-surface);
        color: var(--alv-ink);
        text-decoration: none;
      }""",
    """      /* UNSCOPED, and colour only. A tone is not bar behaviour: the same
         four names have to work in a modal footer, a report header and a
         card. Sizing stays with whoever owns the layout - the bar rule
         above, or Bootstrap's .btn / .btn-sm everywhere else. Setting
         padding here would have inflated the small "quick add" buttons
         inside the Add Asset modal.

         PAIRED WITH .btn ON PURPOSE. A bare `.action-secondary` is (0,1,0)
         and TIES with a page's own `.btn-info` - and a page's <style> sits
         later in the document than base.html, so the page wins. Measured
         on Properties, which has not joined yet: unscoping alone turned
         Help, Map View and Back from outlined/quiet to solid teal. Every
         button in this system carries .btn, so `.btn.action-secondary` at
         (0,2,0) restores the reach WITHOUT losing the argument. Same trap
         as "the shade that got away", approached from the other side. */
      .action-primary,
      .btn.action-primary {
        background: var(--alv-accent);
        border: 1px solid var(--alv-accent);
        color: var(--alv-on-accent);
      }
      .action-primary:hover,
      .action-primary:focus,
      .btn.action-primary:hover,
      .btn.action-primary:focus {
        background: var(--alv-accent-ink);
        border-color: var(--alv-accent-ink);
        color: var(--alv-on-accent);
        text-decoration: none;
      }

      .action-secondary,
      .btn.action-secondary {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        color: var(--alv-ink);
      }
      .action-secondary:hover,
      .action-secondary:focus,
      .btn.action-secondary:hover,
      .btn.action-secondary:focus {
        background: var(--alv-surface);
        color: var(--alv-ink);
        text-decoration: none;
      }""",
    lambda t: re.search(r'\n      \.action-primary\s*,', t) is not None)

sub(B, '  and so does the danger tone',
    """      .page-action-buttons .action-danger {
        background: var(--alv-paper);
        border-color: #f2cecb;
        color: var(--alv-danger);
      }
      .page-action-buttons .action-danger:hover,
      .page-action-buttons .action-danger:focus {""",
    """      .action-danger,
      .btn.action-danger {
        background: var(--alv-paper);
        border: 1px solid #f2cecb;
        color: var(--alv-danger);
      }
      .action-danger:hover,
      .action-danger:focus,
      .btn.action-danger:hover,
      .btn.action-danger:focus {""",
    lambda t: re.search(r'\n      \.action-danger\s*,', t) is not None)

sub(B, '  and Back',
    """      .page-action-buttons .action-back {
        background: transparent;
        border-color: transparent;
        color: var(--alv-ink-soft);
      }
      .page-action-buttons .action-back:hover,
      .page-action-buttons .action-back:focus {""",
    """      /* .back-button is what four report pages call theirs. Same thing,
         different name, so it gets the same treatment rather than a
         rewrite of four templates' markup. */
      .action-back,
      .back-button,
      .btn.action-back,
      .btn.back-button {
        background: transparent;
        border: 1px solid transparent;
        color: var(--alv-ink-soft);
      }
      .action-back:hover,
      .action-back:focus,
      .back-button:hover,
      .back-button:focus,
      .btn.action-back:hover,
      .btn.back-button:hover {""",
    lambda t: '.back-button {' in t or '.back-button,' in t)

# ------------------------------------------------------------- print chrome
sub(B, 'and paper stops printing the furniture',
    """      @media print {
        .alv-table { font-size: 10.5pt; }""",
    """      @media print {
        /* Interactive furniture does not belong on paper. Property Assets
           printed its Add Asset button, its Back arrow and its Group-by
           toggle before this rule existed.

           Naming a few page-specific classes here is deliberate: a page
           cannot add itself to a base.html print rule, and these are the
           only kinds of furniture the system has. .no-print is the escape
           hatch for anything this list does not know about. */
        .page-action-buttons,
        .action-more-wrapper,
        .action-more-menu,
        .back-button,
        .view-toggle-row,
        .filter-panel,
        .search-row,
        .modal,
        .modal-backdrop,
        .alert-dismissible .close,
        .mobile-action-bar,
        .no-print { display: none !important; }

        .alv-table { font-size: 10.5pt; }""",
    '.no-print { display: none !important; }')


# =====================================================================
# 2.  modal footers - the confirm is the primary, Cancel is outlined
# =====================================================================
# Counted, not guessed: property_assets has ONE full-size confirm and THREE
# btn-sm quick-adds, which the next block handles separately.
# The marker is "the OLD string is gone", not "the new one is present".
# `class="btn action-primary"` was already in asset_detail.html - the action
# round put it on Edit Asset - so a presence marker reported the swap as
# already done and left two green buttons behind. For a bulk replace the
# absence of what you are replacing IS the mechanism.
gone = lambda old: (lambda t: old not in t)   # noqa: E731

for name, n_cancel, n_ok in (('asset_detail.html', 4, 2),
                             ('property_assets.html', 1, 1),
                             ('suppliers.html', 1, 0)):
    subn(name, 'Cancel / Close becomes an outlined secondary',
         'class="btn btn-secondary"', 'class="btn action-secondary"',
         gone('class="btn btn-secondary"'), n_cancel)
    if n_ok:
        subn(name, '  and the confirm becomes the primary',
             'class="btn btn-success"', 'class="btn action-primary"',
             gone('class="btn btn-success"'), n_ok)

subn('property_assets.html', '  including the small quick-add confirms',
     'class="btn btn-success btn-sm"', 'class="btn action-primary btn-sm"',
     gone('class="btn btn-success btn-sm"'), 3)

sub('asset_detail.html', '  Download keeps its weight, loses its Bootstrap name',
    'id="invoiceDownloadLink" href="#" class="btn btn-info" target="_blank"',
    'id="invoiceDownloadLink" href="#" class="btn action-primary" '
    'target="_blank"',
    gone('id="invoiceDownloadLink" href="#" class="btn btn-info"'))

sub('suppliers.html', '  and Delete Permanently takes the danger tone',
    'class="btn btn-danger"', 'class="btn action-secondary action-danger"',
    gone('class="btn btn-danger"'))


# =====================================================================
# 3.  the four report Backs, and Edit Supplier
# =====================================================================
for name in BACKS:
    sub(name, 'Back goes quiet',
        'class="btn btn-info back-button"', 'class="btn back-button"',
        gone('class="btn btn-info back-button"'))

# suppliers_edit.html already carries the right names; it just also carries
# the Bootstrap colour. It joins by deletion alone.
sub('suppliers_edit.html', 'Save is the primary, Back is quiet',
    'class="btn btn-info action-primary"', 'class="btn action-primary"',
    gone('class="btn btn-info action-primary"'))
sub('suppliers_edit.html', '  and Back stops being teal too',
    'class="btn btn-info action-back"', 'class="btn action-back"',
    gone('class="btn btn-info action-back"'))

# The four reports keep their own .back-button layout rules (position,
# padding); base.html now supplies only the colour. Nothing is deleted here.


# =====================================================================
# 3b. edit_asset.html - the one page that joined nothing
# =====================================================================
# A yellow bg-warning card header, a Back that calls itself
# `action-btn-back` (so no rule this project wrote ever reached it), and a
# green Save beside a grey Cancel in a form footer. Three surfaces, one
# page.
E = 'edit_asset.html'

sub(E, 'the form card loses its yellow bar and leads with the asset',
    """<div class="card form-card">
    <div class="card-header bg-warning text-white">
        <h4 class="mb-0"><i class="fas fa-edit"></i> Edit: {{ asset.name }}</h4>
    </div>
    <div class="card-body">""",
    """<div class="alv-card alv-card-lead form-card">
    <div class="alv-card-head">
        <h4 class="alv-card-title mb-0"><i class="fas fa-edit"></i> Edit: {{ asset.name }}</h4>
    </div>
    <div class="alv-card-body card-body">""",
    gone('card-header bg-warning'))

# `action-btn-back` is the same component under a name nothing matches. It
# gets the standard name; the page's own width:100% override goes with it,
# because base.html already decides what Back does on a phone.
sub(E, '  Back takes the standard name, and goes quiet',
    'class="btn btn-info action-btn-back"', 'class="btn action-back"',
    gone('action-btn-back'))

sub(E, '  Save is the primary of a form',
    'class="btn btn-success"', 'class="btn action-primary"',
    gone('class="btn btn-success"'))
sub(E, '  and Cancel is outlined beside it',
    'class="btn btn-secondary"', 'class="btn action-secondary"',
    gone('class="btn btn-secondary"'))

# Deleted by SELECTOR, not by a literal. The first draft matched a
# one-line `.action-btn-back { width: 100%; ... }` copied out of a report
# that had already collapsed the whitespace; the file has it across five
# lines, so nothing matched and the class survived into the self-check.
_dead_n = 0
for _sel in (r'\.form-card \.card-header h4', r'\.action-btn-back'):
    _new, _k = re.subn(r'\n[ \t]*%s[^{}]*\{[^}]*\}' % _sel, '', src[E])
    if _k:
        src[E] = _new
        _dead_n += _k
if _dead_n:
    CHANGES.append((E, 'apply', '  dropped %d rules base.html now owns'
                    % _dead_n))


# =====================================================================
# 4.  verify before writing
# =====================================================================
problems = []
BB = src[B]
_i = BB.find('--alv-table-std')
_blk = re.sub(r'/\*.*?\*/', ' ', BB[_i:BB.find('</style>', _i)], flags=re.S)

if _blk.count('{') != _blk.count('}'):
    problems.append('base.html: braces no longer balance (%d/%d)'
                    % (_blk.count('{'), _blk.count('}')))
for want in ('.action-primary', '.action-secondary', '.action-danger',
             '.action-back', '.back-button'):
    if not re.search(r'(?<![\w-])%s(?![\w-])[^{}]*\{' % re.escape(want), _blk):
        problems.append('base.html: %s is not defined' % want)
# The tones must be UNSCOPED now, or the modal footers get nothing.
for tone in ('.action-primary', '.action-secondary', '.action-danger'):
    # Top-level selector: the name starts a line inside the block, followed
    # by a comma (it shares the rule with its .btn. twin) or by the brace.
    if not re.search(r'\n      %s\s*[,{]' % re.escape(tone), _blk):
        problems.append('base.html: %s is still bar-scoped' % tone)
    # ...and the paired .btn. selector must exist, or a page's own .btn-info
    # ties on specificity and wins on document order.
    if '.btn%s' % tone not in _blk:
        problems.append('base.html: %s has no .btn-paired twin - a page with '
                        'its own .btn-info would beat it' % tone)
# ...and must not set padding, or btn-sm stops meaning anything.
for tone in ('.action-primary', '.action-secondary', '.action-danger',
             '.action-back'):
    m = re.search(r'\n      %s[^{}]*\{([^}]*)\}' % re.escape(tone), _blk)
    if m and 'padding' in m.group(1):
        problems.append('base.html: %s sets padding - btn-sm would be '
                        'overridden' % tone)
if 'display: none !important' not in _blk:
    problems.append('base.html: the print block hides nothing')

for name in MODALS:
    if 'btn-success' in src[name]:
        problems.append('%s: a green confirm survived' % name)
    if 'class="btn btn-secondary"' in src[name]:
        problems.append('%s: a solid grey Cancel survived' % name)
for name in BACKS:
    if 'btn-info back-button' in src[name]:
        problems.append('%s: Back is still filled' % name)
if 'btn-info action-' in src['suppliers_edit.html']:
    problems.append('suppliers_edit.html: a Bootstrap colour survived')
for bad in ('bg-warning', 'btn-success', 'btn-info action-', 'action-btn-back'):
    if bad in src['edit_asset.html']:
        problems.append('edit_asset.html: %s survived' % bad)
if 'alv-card alv-card-lead form-card' not in src['edit_asset.html']:
    problems.append('edit_asset.html: the form card did not join')

for name in FILES:
    t = src[name]
    if t.count('{%') != t.count('%}'):
        problems.append('%s: Django tags do not balance' % name)
    for i_, line in enumerate(t.split('\n'), 1):
        if '{#' in line and '#}' not in line:
            problems.append('%s: unclosed {# comment at line %d' % (name, i_))
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I):
        b = re.sub(r'/\*.*?\*/', ' ', m.group(1), flags=re.S)
        if b.count('{') != b.count('}'):
            problems.append('%s: CSS braces do not balance' % name)
# data-dismiss is what closes a modal; losing it strands the dialog.
if src['asset_detail.html'].count('data-dismiss="modal"') < 4:
    problems.append('asset_detail.html: a modal lost its dismiss handler')

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
cur = None
for name, kind, label in CHANGES:
    if name != cur:
        print('  %s' % name)
        cur = name
    print('    %-7s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')
print('  Tones now work in a bar, a modal footer and a report header.')
print('  Layout and the mobile collapse stay with .page-action-buttons.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

for name in FILES:
    p = os.path.join(TPL, name)
    bak = p + '.bak_btnreach'
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    enc, nl = meta[name]
    with io.open(p, 'w', encoding=enc, newline='') as fh:
        fh.write(src[name].replace('\n', nl) if nl != '\n' else src[name])
    print('  wrote pages/templates/%s' % name)
print('')
print('Now run:  python test_button_reach.py')
