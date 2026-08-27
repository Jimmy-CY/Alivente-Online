"""apply_action_standard - the page-header action bar gets a home.

    python apply_action_standard.py --check
    python apply_action_standard.py

Run AFTER apply_detail_property.py.

WHY
---
`Show-ActionButtons.py` measured it: **19 templates, 115 rules**, and
base.html defines exactly none of them. The page-header bar is the last
shared component in the system with no single home - the same shape the
tables were in before this project started.

It is not only colour. The mobile half is a real responsive pattern, copied
nineteen times: at 768px the secondary actions disappear, the primary flexes
to fill the row, Back shrinks to a 44px icon and a 44px "More" menu takes
what was hidden. That is worth hoisting on its own.

WHAT COLOUR MEANS TODAY - measured, not assumed
-----------------------------------------------
    btn-info 60   btn-secondary 26   btn-success 13   btn-danger 9
    btn-warning 6   btn-light 4   btn-primary 2

Nothing. `btn-warning` is yellow on six buttons across four pages and means
"edit" on exactly one of them. Six pages use two or more colours in the same
bar.

THE RULE: WEIGHT, NOT VERB
--------------------------
    .action-primary    solid accent - the page's main verb, at most one
    .action-secondary  outlined - supporting actions
    .action-danger     a TONE, worn with -primary or -secondary. Outlined,
                       and it fills red only on hover - which is exactly
                       what .icon-delete already does in every table row
    .action-back       quiet - navigation, not an action on the data

Green leaves the button vocabulary entirely. `--alv-good` already means
"Active" on the pill scale, and a green Save button beside a green Active
pill makes the colour mean two things.

HOW A PAGE JOINS
----------------
By DELETING. The class names are the ones that already exist, so a page
joins by dropping the Bootstrap colour class from its markup and its local
copy of the layout from its CSS:

    class="btn btn-warning action-primary"   ->   class="btn action-primary"

asset_detail.html is the pilot here. Position does not change on any page:
actions stay left, Back stays right.

Idempotent. Backs up to .bak_actionstd.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

FILES = ('base.html', 'asset_detail.html')

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

if '--alv-card-std' not in src['base.html']:
    sys.exit('! base.html has no card component - apply_card_standard.py first.')
if 'alv-card alv-card-lead' not in src['asset_detail.html']:
    sys.exit('! asset_detail.html is not on the card standard yet - '
             'apply_detail_property.py first.')

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


# =====================================================================
# 1.  base.html - the component
# =====================================================================
BAR = """
      /* ================================================================
         The page-header action bar                     --alv-actions-std

         Nineteen templates carried a copy of this, 115 rules between
         them, and base.html carried none of it. The names below are the
         ones those pages already use, so a page joins by DELETING its
         copy rather than by being rewritten.

         Colour is by WEIGHT, not by verb. A page has one main thing you
         came to do; that is the solid one. Everything else is outlined.
         Measured before deciding: btn-info 60, btn-secondary 26,
         btn-success 13, btn-danger 9, btn-warning 6 - which is to say
         the colours meant nothing.
         ================================================================ */
      .page-action-buttons {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
      }
      /* Back is navigation, not an action on the data, so it sits apart
         from the verbs. Actions left, Back right - unchanged, so no
         page's layout moves when it joins. */
      .page-action-buttons .action-back { margin-left: auto; }

      .page-action-buttons .btn,
      .page-action-buttons .action-primary,
      .page-action-buttons .action-secondary,
      .page-action-buttons .action-back {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: var(--alv-radius);
        font-family: var(--alv-font-ui);
        font-size: 14px;
        font-weight: 600;
        line-height: 1.2;
        border: 1px solid transparent;
        white-space: nowrap;
        text-decoration: none;
      }

      .page-action-buttons .action-primary {
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
      }

      /* A TONE, not a position - worn alongside -primary or -secondary,
         so a destructive button keeps whatever layout behaviour its
         position class gives it. Outlined at rest and red only on hover:
         the same bargain .icon-action-btn.icon-delete already strikes in
         every table row, one level up. */
      .page-action-buttons .action-danger {
        background: var(--alv-paper);
        border-color: #f2cecb;
        color: var(--alv-danger);
      }
      .page-action-buttons .action-danger:hover,
      .page-action-buttons .action-danger:focus {
        background: var(--alv-danger);
        border-color: var(--alv-danger);
        color: #fff;
        text-decoration: none;
      }

      .page-action-buttons .action-back {
        background: transparent;
        border-color: transparent;
        color: var(--alv-ink-soft);
      }
      .page-action-buttons .action-back:hover,
      .page-action-buttons .action-back:focus {
        background: var(--alv-surface);
        color: var(--alv-ink);
        text-decoration: none;
      }

      .page-action-buttons .btn:focus-visible,
      .page-action-buttons .action-back:focus-visible {
        outline: 2px solid var(--alv-accent);
        outline-offset: 2px;
      }

      /* Copied onto sixteen pages, defined in none of them twice the
         same. pointer-events matters: without it a "disabled" anchor is
         still a working link. */
      .disabled-btn {
        opacity: .6;
        cursor: not-allowed;
        pointer-events: none;
      }

      .action-more-wrapper { display: none; }

      @media (max-width: 768px) {
        /* The half worth hoisting. One row, always: the primary takes the
           space, the secondaries move into the More menu, and Back keeps
           a 44px target. */
        .page-action-buttons {
          flex-direction: row;
          flex-wrap: nowrap;
          gap: 8px;
          width: 100%;
        }
        .page-action-buttons .action-primary {
          flex: 1 1 auto;
          min-width: 0;
          height: 38px;
        }
        .page-action-buttons .action-secondary { display: none; }
        .page-action-buttons .action-back {
          margin-left: 0;
          flex: 0 0 auto;
          width: 44px;
          height: 38px;
          padding: 0;
        }
        .page-action-buttons .action-back .action-back-label { display: none; }

        .action-more-wrapper {
          display: block;
          position: relative;
          flex: 0 0 auto;
        }
        /* Scoped to the bar, or the generic
           `.page-action-buttons .btn { border-color: transparent }` above
           wins on specificity (0,2,0 beats 0,1,0) and the More button
           becomes a white box on white. Measured, not guessed. */
        .page-action-buttons .action-more-btn {
          width: 44px;
          height: 38px;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--alv-paper);
          border: 1px solid var(--alv-line);
          border-radius: var(--alv-radius);
          color: var(--alv-ink);
        }
        .page-action-buttons .action-more-btn:hover,
        .page-action-buttons .action-more-btn:focus {
          background: var(--alv-surface);
          color: var(--alv-ink);
        }
        .action-more-menu {
          position: absolute;
          top: calc(100% + 6px);
          right: 0;
          z-index: 1030;
          min-width: 200px;
          background: var(--alv-paper);
          border: 1px solid var(--alv-line);
          border-radius: var(--alv-radius);
          box-shadow: 0 8px 20px -8px rgba(16, 34, 40, .28);
          padding: 6px;
        }
        .action-more-item {
          display: flex;
          align-items: center;
          gap: 12px;
          width: 100%;
          padding: 10px 12px;
          border: 0;
          background: transparent;
          border-radius: var(--alv-radius);
          font-size: 14px;
          color: var(--alv-ink);
          text-align: left;
          text-decoration: none;
        }
        .action-more-item i {
          color: var(--alv-accent);
          width: 18px;
          text-align: center;
          flex-shrink: 0;
        }
        .action-more-item:hover,
        .action-more-item:focus {
          background: var(--alv-surface);
          color: var(--alv-ink);
          text-decoration: none;
        }
        .action-more-item-danger { color: var(--alv-danger); }
        .action-more-item-danger i { color: var(--alv-danger); }
      }
"""

if '--alv-actions-std' in src['base.html']:
    CHANGES.append(('base.html', 'skip', 'the page-header action bar'))
else:
    i = src['base.html'].find('--alv-table-std')
    j = src['base.html'].find('</style>', i)
    if j < 0:
        sys.exit('! could not find the end of the standard block')
    src['base.html'] = (src['base.html'][:j] + BAR + '    '
                        + src['base.html'][j:])
    CHANGES.append(('base.html', 'apply', 'the page-header action bar'))


# =====================================================================
# 2.  asset_detail.html - the pilot
# =====================================================================
D = 'asset_detail.html'

sub(D, 'Edit is the primary, and stops being yellow',
    '<a href="{% url \'edit_asset\' asset.id %}" class="btn btn-warning action-primary">',
    '<a href="{% url \'edit_asset\' asset.id %}" class="btn action-primary">',
    'class="btn action-primary">')

sub(D, '  Delete keeps its place and takes the danger TONE',
    '<button type="button" class="btn btn-danger action-secondary" onclick="confirmDelete()">',
    '<button type="button" class="btn action-secondary action-danger" onclick="confirmDelete()">',
    'action-secondary action-danger" onclick="confirmDelete()"')

sub(D, '  and so do both disabled twins',
    """        <span class="btn btn-warning action-primary disabled-btn">
            <i class="fas fa-edit"></i> Edit Asset
        </span>
        <span class="btn btn-danger action-secondary disabled-btn">""",
    """        <span class="btn action-primary disabled-btn">
            <i class="fas fa-edit"></i> Edit Asset
        </span>
        <span class="btn action-secondary action-danger disabled-btn">""",
    'class="btn action-primary disabled-btn"')

sub(D, '  Back goes quiet',
    'class="btn btn-info action-back" role="button" aria-label="Back"',
    'class="btn action-back" role="button" aria-label="Back"',
    'class="btn action-back" role="button"')

sub(D, '  and the mobile More button loses its fill',
    'class="btn btn-info action-more-btn"',
    'class="btn action-more-btn"',
    'class="btn action-more-btn"')

# ---------------------------------------------------- delete what base owns
DEAD = ('.page-action-buttons', '.action-primary', '.action-secondary',
        '.action-add-new', '.action-back', '.action-more-btn',
        '.action-more-menu', '.action-more-item', '.action-more-wrapper',
        '.disabled-btn')


def strip_css_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).strip()


def top_rules(block, offset=0):
    i, n, s0 = 0, len(block), 0
    while i < n:
        if block[i] == '{':
            selector = block[s0:i]
            depth, j = 1, i + 1
            while j < n and depth:
                if block[j] == '{':
                    depth += 1
                elif block[j] == '}':
                    depth -= 1
                j += 1
            yield (strip_css_comments(selector).startswith('@'), selector,
                   s0 + offset, j + offset, i + offset, j - 1 + offset)
            i = j
            s0 = i
        else:
            i += 1


def is_dead(one):
    s = strip_css_comments(one)
    if not s or s.startswith('@'):
        return False
    parts = re.findall(r'\.[A-Za-z0-9_-]+', s)
    if not parts:
        return False
    # .action-back-label is a child of the component but NOT owned - it is
    # the text inside Back, and base.html only hides it on mobile. The
    # boundary in `parts` keeps it distinct from .action-back, which a
    # plain \b would not have.
    return all(p in DEAD for p in parts)


already = '--alv-actions-std' in src['base.html'] and \
    'btn-warning action-primary' not in src[D]
m = re.search(r'(<style[^>]*>)(.*?)(</style>)', src[D], re.S | re.I)
if not m:
    sys.exit('! asset_detail.html has no <style> block')
css = m.group(2)
cuts = []


def scan(block, offset):
    for at, selector, s0, s1, b0, b1 in top_rules(block, offset):
        if at:
            scan(css[b0 + 1:b1], b0 + 1)
            continue
        sels = [x for x in strip_css_comments(selector).split(',') if x.strip()]
        if sels and all(is_dead(x) for x in sels):
            cuts.append((s0, s1))


scan(css, 0)
if cuts:
    out, prev = [], 0
    for s0, s1 in sorted(cuts):
        out.append(css[prev:s0])
        prev = s1
    out.append(css[prev:])
    new_css = re.sub(r'\n{3,}', '\n\n', ''.join(out))
    src[D] = (src[D][:m.start()] + m.group(1) + new_css + m.group(3)
              + src[D][m.end():])
    CHANGES.append((D, 'apply', 'deleted %d rules base.html now owns'
                    % len(cuts)))
elif already:
    CHANGES.append((D, 'skip', 'CSS deletion'))
else:
    sys.exit('! asset_detail.html: nothing matched for deletion - '
             'the dead set is wrong')


# =====================================================================
# 3.  verify before writing
# =====================================================================
problems = []
B, T = src['base.html'], src[D]

_i = B.find('--alv-table-std')
_blk = strip_css_comments(B[_i:B.find('</style>', _i)])
if _blk.count('{') != _blk.count('}'):
    problems.append('base.html: braces no longer balance (%d/%d)'
                    % (_blk.count('{'), _blk.count('}')))
for want in ('.page-action-buttons', '.action-primary', '.action-secondary',
             '.action-danger', '.action-back', '.action-more-btn',
             '.disabled-btn'):
    if want not in _blk:
        problems.append('base.html: %s is missing' % want)
if 'pointer-events: none' not in _blk:
    problems.append('base.html: .disabled-btn without pointer-events is a '
                    'working link that looks disabled')

for bad in ('btn-warning', 'btn-success', 'btn-light'):
    if re.search(r'class="[^"]*%s[^"]*action-' % bad, T) or \
            re.search(r'class="[^"]*action-[^"]*%s' % bad, T):
        problems.append('%s: %s still colours a bar button' % (D, bad))
if T.count('action-primary') < 2:
    problems.append('%s: the primary or its disabled twin went missing' % D)
if T.count('action-danger') < 2:
    problems.append('%s: Delete lost its danger tone on one branch' % D)
if T.count('perms.auth.can_edit_properties') < 3:
    problems.append('%s: a permission conditional went missing' % D)
if 'confirmDelete()' not in T or 'edit_asset' not in T:
    problems.append('%s: an action target was lost' % D)
_c = strip_css_comments(''.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                           T, re.S | re.I)))
if _c.count('{') != _c.count('}'):
    problems.append('%s: CSS braces do not balance' % D)
for i_, line in enumerate(T.split('\n'), 1):
    if '{#' in line and '#}' not in line:
        problems.append('%s: unclosed {# comment at line %d' % (D, i_))

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
before = len(open(os.path.join(TPL, D), encoding=meta[D][0],
                  errors='replace').read().replace('\r\n', '\n').split('\n'))
after = len(src[D].split('\n'))
print('  %-24s %4d -> %4d lines  (%d removed)' % (D, before, after,
                                                  before - after))
print('')
print('  Position is unchanged: actions left, Back right.')
print('  18 templates still to join. See Show-ActionButtons.py.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

for name in FILES:
    p = os.path.join(TPL, name)
    bak = p + '.bak_actionstd'
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    enc, nl = meta[name]
    with io.open(p, 'w', encoding=enc, newline='') as fh:
        fh.write(src[name].replace('\n', nl) if nl != '\n' else src[name])
    print('  wrote pages/templates/%s' % name)
print('')
print('Now run:  python test_action_standard.py')
