"""apply_heading_components.py - base takes over the three classes the
   standard is written in, and every page stops hand-writing them.

    python apply_heading_components.py --check     survey, write nothing
    python apply_heading_components.py             apply

Run from the repo root.

THE PROBLEM

  page-title-h2, page-subtitle-h4 and page-action-buttons-form are the
  class names base.html's own standards block is written in, and base
  DECLARES NONE OF THEM. Every page that wanted one wrote it out. That is
  the same fault the button sweep found in the action bars, one layer up:
  base reached the names but not the rules.

WHAT THE DRIFT ACTUALLY IS - it is not thirteen designs

  Read as declarations it looks like scattered improvisation. Read as a
  RULE it is one rule, hand-derived on every page, and a few pages got it
  wrong:

      h2 margin-bottom    a subtitle follows      pages
      0                   yes                     22
      1rem                NO                       6
      0                   NO                       2   <- wrong
      0.25rem             yes                      2   <- wrong
      1rem                yes                      1   <- wrong

  The gap closes when a subtitle follows the heading and opens when
  nothing does. Thirty pages worked that out independently; five did not.
  base can say it in one line, and the five become right rather than
  becoming exceptions. AGREED 16 Sep: correct them.

THREE DECISIONS TAKEN BEFORE ANY OF THIS WAS WRITTEN

  1. THE SUBTITLE IS SOFT GREY, from var(--alv-ink-soft). Six rules paint
     it with the literal #6c757d - Bootstrap's grey-600, from no palette
     this project defines - and nineteen leave it inheriting. One of those
     groups had to move. The subtitle is a MODE LABEL under a module name,
     so a quieter tone is the hierarchy the shape-B round already chose in
     words; this makes it true in colour.

  2. THE <center> ELEMENTS GO. Thirty-four pages centre the heading with a
     <center> element inside the h2. base centres with text-align, so they
     are redundant the moment it does. This turns a CSS round into a
     markup round on signed-off pages, so every page is checked two ways
     that its own construction cannot fake: the surviving CSS rules must
     be exactly what was there minus these three classes, and the page's
     visible words must be character-for-character unchanged.

  3. THE FIVE OUTLIERS ARE CORRECTED, not preserved. A component with five
     documented exceptions on the day it ships is not a component.

AND IT TAKES A LARGE BITE OUT OF THE PAPER BUG, FOR FREE

  A max-width query with no `screen` keyword applies to PAPER as well as
  to screens - A4 portrait is about 718 CSS px, inside every 768px query -
  which is why printed reports come out with a phone-sized heading. The
  page-local phone rules for these three classes sit in exactly such
  queries on nineteen pages, and this round DELETES those rules. base's
  replacement says `screen and`. The hoist and that part of the sweep are
  the same edit; doing them separately would mean opening the same pages
  twice.

  It does NOT sweep the other naked queries on those pages. They belong to
  section 2.I, they are about different components, and a round that
  changes two things cannot say which one fixed it.

NOTHING HERE IS HARDCODED TO A PAGE

  The list of pages is derived from the corpus at runtime, because the
  build sandbox holds about half this repo's templates and a list chosen
  from half a corpus is a list chosen from the wrong corpus. --check
  prints what it would do, file by file, and writes nothing.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUITE = 'test_heading_components.py'
SUFFIX = '.bak_hcomp'
MARK = 'ALV PAGE HEADING v1'

CLASSES = ('page-title-h2', 'page-subtitle-h4', 'page-action-buttons-form')

# base's side of the round. One definition each, the conditional stated
# once, and the phone rules qualified with `screen` so they stay off paper.
BLOCK = """
/* ===== ALV PAGE HEADING v1 ===== */
/* The three classes base's own standards block is written in, which base
   did not declare until now. Every page that wanted one wrote it out: 33
   copies of the h2 rule, 26 of the subtitle, 12 of the form bar.

   THE BOTTOM MARGIN IS CONDITIONAL, and that is the whole of the apparent
   drift. The gap closes when a subtitle follows the heading and opens when
   nothing does - thirty pages worked that out one at a time, and five got
   it wrong. Said once, here, it cannot be got wrong again.

   The subtitle takes --alv-ink-soft. Six pages painted it #6c757d, which
   is Bootstrap's grey and belongs to no palette this project defines. A
   mode label under a module name should be the quieter of the two, which
   is what the shape-B round decided in words. */
.page-title-h2 {
    text-align: center;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
}
.page-title-h2:has(+ .page-subtitle-h4) { margin-bottom: 0; }

.page-subtitle-h4 {
    text-align: center;
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    color: var(--alv-ink-soft);
}

/* The form action bar. base already owns .page-action-buttons; this is the
   variant the entry screens use, and it differed only in where it pushes
   its buttons. */
.page-action-buttons-form { justify-content: flex-end; }

/* SCREEN AND, not a bare max-width. A4 portrait is about 718 CSS px, so a
   bare query fires on paper and prints every report with a phone-sized
   heading. Nineteen pages carried exactly that around these three classes;
   their copies went with this round. */
@media screen and (max-width: 768px) {
    .page-title-h2    { font-size: 1.25rem; }
    .page-subtitle-h4 { font-size: 1rem; margin-bottom: 0.75rem; }

    .page-action-buttons-form {
        display: flex;
        flex-direction: row;
        gap: 8px;
        width: 100%;
        flex-wrap: nowrap;
        align-items: stretch;
        margin-bottom: 1rem;
    }
    .page-action-buttons-form .action-primary {
        flex: 1 1 auto;
        min-width: 0;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 0 12px;
        font-size: 13px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
    }
    .page-action-buttons-form .action-back {
        flex: 0 0 auto;
        width: 44px;
        height: 38px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0;
    }
}
"""


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n.endswith('.html'):
                out.append(os.path.join(dirpath, n))
    return sorted(out)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


def style_spans(text):
    """(start, end) of the CONTENT of every style element."""
    return [(m.start(1), m.end(1))
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def targets_in(css, offset):
    """Spans to delete from one stylesheet, and the media blocks emptied.

    Brace-aware, and it records positions rather than rewriting text, so
    everything it does not name comes through byte for byte.
    """
    # BLANK THE COMMENTS FIRST, to spaces of the same length so every
    # offset below still points at the real file.
    #
    # The first draft scanned the raw text, and a brace inside a CSS
    # comment desynchronised the media tracking: it decided a media block
    # was empty when it was not, deleted the whole block, and orphaned
    # thirty unrelated rules. Caught by the rule-set check rather than by
    # reading, which is the only reason it is not in the commit.
    #
    # Prose shaped like code, for the twenty-somethingth time, this time
    # inside the tool doing the sweep.
    scan = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css,
                  flags=re.S)

    drop = []                 # (start, end) absolute
    media_open = None         # (abs_start_of_at, abs_start_of_body)
    kept_in_media = 0
    dropped_in_media = 0
    empties = []
    i = 0
    for m in re.finditer(r'@media([^{]*)\{|([^{}]+)\{([^{}]*)\}|\}', scan):
        if m.group(1) is not None:
            media_open = (m.start(), m.end())
            kept_in_media = dropped_in_media = 0
        elif m.group(0) == '}':
            if media_open and dropped_in_media and not kept_in_media:
                empties.append((offset + media_open[0], offset + m.end()))
            media_open = None
        else:
            sel = css[m.start(2):m.end(2)] if m.group(2) else ''
            hit = any('.' + c in sel for c in CLASSES)
            if media_open:
                if hit:
                    dropped_in_media += 1
                else:
                    kept_in_media += 1
            if hit:
                # ANCHOR ON THE SELECTOR, not on where the match began.
                #
                # The rule regex starts matching immediately after the
                # PREVIOUS rule's closing brace, so m.start() sits on the
                # newline after it. Expanding that to whole lines reached
                # backwards into the rule before - and, for the first rule
                # inside a media block, swallowed the `@media ... {` line
                # and orphaned its closing brace. The spans overlapped and
                # the splice quietly mangled the file.
                raw_sel = m.group(2) or ''
                start = m.start(2) + len(raw_sel) - len(raw_sel.lstrip())
                # Take a comment sitting immediately above it, but only if
                # that comment is about one of these classes. A comment can
                # cover several rules, and deleting one that explains the
                # rule below would leave the next reader with prose about
                # something that is no longer there.
                head = css[:start]
                cm = re.search(r'/\*((?:(?!\*/).)*)\*/\s*$', head, re.S)
                if cm and any(c in cm.group(1) for c in CLASSES):
                    start = cm.start()
                # WHOLE LINES, both ends. The first draft trimmed spaces off
                # the front and took at most one newline off the back, and
                # the result glued a media opener to the rule after it:
                #
                #     @media (max-width: 768px) {    .action-back-label {
                #
                # A round that deletes a rule and reflows the file around it
                # cannot say it deleted only what it named.
                # Whole lines, but ONLY when the rule has its line to
                # itself. A rule sharing a line with anything else takes
                # its exact span and nothing more.
                line0 = scan.rfind('\n', 0, start) + 1
                if not scan[line0:start].strip():
                    start = line0
                end = m.end()
                nxt = scan.find('\n', end)
                if nxt >= 0 and not scan[end:nxt].strip():
                    end = nxt + 1
                drop.append((offset + start, offset + end))
    # a media block that empties wholly replaces the individual drops
    for a, b in empties:
        drop = [(s, e) for s, e in drop if not (a <= s and e <= b)]
        drop.append((a, b))
    # MERGE, unconditionally. Overlapping spans are what broke the first
    # draft, and a splice that assumes they cannot overlap is a splice
    # that corrupts a file the day they do.
    merged = []
    for a, b in sorted(drop):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged, len(empties)


CENTER = re.compile(
    r'(<h[24][^>]*class="[^"]*\bpage-(?:title-h2|subtitle-h4)\b[^"]*"[^>]*>)'
    r'(.*?)(</h[24]>)', re.S)


def strip_centers(text):
    """Remove <center> from inside the two headings, and only there.

    Not a global sweep. Other pages use <center> for other things and this
    round has no opinion about those.
    """
    n = [0]

    def one(m):
        inner = m.group(2)
        if '<center' not in inner.lower():
            return m.group(0)
        n[0] += len(re.findall(r'</?center[^>]*>', inner, re.I))
        return m.group(1) + re.sub(r'</?center[^>]*>', '', inner,
                                   flags=re.I) + m.group(3)
    return CENTER.sub(one, text), n[0]


def rule_set(text):
    """Every CSS rule in the file as (media, selector, declaration).

    A multiset, not a diff. It is what makes the check below independent:
    the round is CONSTRUCTED by deleting spans, so comparing the result to
    "the original minus those spans" proves nothing at all - it restates
    the construction. Comparing the RULES that survive against the rules
    that were there is a different measurement of the same file.
    """
    out = []
    for a, b in style_spans(text):
        css = re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
        media = None
        for m in re.finditer(r'@media([^{]*)\{|([^{}]+)\{([^{}]*)\}|\}', css):
            if m.group(1) is not None:
                media = ' '.join(m.group(1).split())
            elif m.group(0) == '}':
                media = None
            else:
                out.append((media, ' '.join(m.group(2).split()),
                            ' '.join(m.group(3).split())))
    return out


def words_of(text):
    """The page's visible words, with every tag and all whitespace gone.

    The other half of the independent check. Removing a center element
    must not remove a letter, and deleting a stylesheet rule must not
    touch the body at all.
    """
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def plan_page(path):
    text, nl, raw = read(path)
    if MARK in text:
        return None
    spans = style_spans(text)
    drop, empties = [], 0
    for a, b in spans:
        d, e = targets_in(text[a:b], a)
        drop.extend(d)
        empties += e
    stripped, centers = strip_centers(text)
    if not drop and not centers:
        return None

    new = stripped
    if drop:
        # Re-locate the spans in the stripped text. The centre strip only
        # touches markup and the drops only touch stylesheets, so the
        # stylesheet offsets shift by however much markup shrank BEFORE
        # each one. Do the drops on the ORIGINAL and the strip after, so
        # neither has to reason about the other.
        out, last = [], 0
        for a, b in sorted(drop):
            out.append(text[last:a])
            last = b
        out.append(text[last:])
        new, centers = strip_centers(''.join(out))
    return dict(path=path, rel=rel_of(path), text=text, new=new, nl=nl,
                raw=raw, rules=len(drop), empties=empties, centers=centers)


def check_page(p, problems):
    rel, old, new = p['rel'], p['text'], p['new']
    bad = []
    for c in CLASSES:
        for a, b in style_spans(new):
            for m in re.finditer(r'([^{}]+)\{', new[a:b]):
                if '.' + c in m.group(1):
                    bad.append('still styles .%s' % c)
                    break
    # The markup must still USE what base now styles.
    for c in CLASSES:
        if re.search(r'class="[^"]*\b%s\b' % c, old) and not \
                re.search(r'class="[^"]*\b%s\b' % c, new):
            bad.append('lost its .%s element' % c)
    for a, b in style_spans(new):
        blk = new[a:b]
        if blk.count('{') != blk.count('}'):
            bad.append('a stylesheet no longer balances its braces')
    for tag in ('div', 'form', 'h2', 'h4', 'table'):
        o = (len(re.findall(r'<%s\b' % tag, old))
             - len(re.findall(r'</%s>' % tag, old)))
        n = (len(re.findall(r'<%s\b' % tag, new))
             - len(re.findall(r'</%s>' % tag, new)))
        if o != n:
            bad.append('<%s> balance moved %+d -> %+d' % (tag, o, n))
    if '<center' in new.lower():
        for m in CENTER.finditer(new):
            if '<center' in m.group(2).lower():
                bad.append('a heading still holds a center element')
                break
    # NOTHING BUT THE NAMED REMOVALS, measured two ways that the
    # construction cannot fake.
    #
    # First: the rules that survive must be exactly the rules that were
    # there, minus the ones about these three classes. A rule lost to a
    # mis-trimmed span shows up here as a rule that has gone missing.
    was = rule_set(old)
    now = rule_set(new)
    keep = [r for r in was if not any('.' + c in r[1] for c in CLASSES)]
    lost = [r for r in keep if r not in now]
    gained = [r for r in now if r not in was]
    if lost:
        bad.append('%d unrelated rule(s) went with it, e.g. %s'
                   % (len(lost), lost[0][1][:40]))
    if gained:
        bad.append('%d rule(s) appeared, e.g. %s'
                   % (len(gained), gained[0][1][:40]))
    # Second: not one visible word moved. Stripping a center element must
    # not take a letter with it, and a stylesheet edit must not reach the
    # body at all.
    if words_of(old) != words_of(new):
        bad.append('the visible text of the page changed')
    if len(new) >= len(old):
        bad.append('the file did not shrink')
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


def plan_base(problems):
    text, nl, raw = read(BASE)
    if MARK in text:
        return None
    at = text.find('.alv-map-nokey {')
    if at < 0:
        problems.append('base: .alv-map-nokey is not there to anchor to - '
                        'run apply_map_provider.py first')
        return None
    end = text.find('}', at)
    tail = text[end + 1:]
    if tail.lstrip()[:8] != '</style>':
        problems.append('base: the anchor rule is no longer the last one in '
                        'its stylesheet')
        return None
    cut = end + 1 + (len(tail) - len(tail.lstrip()))
    new = text[:cut] + BLOCK + text[cut:]
    if new.count(MARK) != 1:
        problems.append('base: the block would land %d times' % new.count(MARK))
        return None
    for a, b in style_spans(new):
        if new[a:b].count('{') != new[a:b].count('}'):
            problems.append('base: a stylesheet would not balance')
            return None
    return dict(path=BASE, rel='base.html', text=text, new=new, nl=nl,
                raw=raw, rules=0, empties=0, centers=0)


def plan_gate(problems):
    """Put the round's suite on the gate, wherever that list now ends.

    NOT anchored on the name of the last suite. This sandbox's copy of the
    push script ends at test_map_provider and the development machine's
    ends thirteen entries later, because gate round two ran there and not
    here. An anchor that names a neighbour is an anchor that works on one
    machine.
    """
    if not os.path.exists(PS1):
        problems.append('Push-PendingChanges.ps1 is not here')
        return None
    text, nl, raw = read(PS1)
    if "'" + SUITE + "'" in text:
        return None
    at = text.find('$suites = @(')
    if at < 0:
        problems.append('the gate has no $suites array to join')
        return None
    close = text.find('\n)\n', at)
    if close < 0:
        problems.append('the $suites array does not close')
        return None
    entry = ("\n\n    # base owns the three classes the standard is written in.\n"
             "    # Its section 3 RENDERS both heading shapes and measures the\n"
             "    # gap, because :has() is the kind of rule that silently does\n"
             "    # nothing. Newest, so most likely to be what breaks.\n"
             "    '" + SUITE + "'")
        # the entry the array's last line needs in order to keep it company
    new = text[:close] + ',' + entry + text[close:]
    if new.count("'" + SUITE + "'") != 1:
        problems.append('the suite would be listed twice')
        return None
    after = new[new.index("'" + SUITE + "'"):]
    if after.split('\n')[1].strip() != ')':
        problems.append('the suite would not land inside the array')
        return None
    return dict(path=PS1, rel='Push-PendingChanges.ps1', text=text, new=new,
                nl=nl, raw=raw, rules=0, empties=0, centers=0)


def main():
    check_only = '--check' in sys.argv
    if not os.path.isdir(T):
        print('! %s not found - run from the repo root' % T)
        sys.exit(1)

    problems = []
    planned = []

    g = plan_gate(problems)
    if g:
        planned.append(g)

    b = plan_base(problems)
    if b:
        planned.append(b)
    elif not problems:
        print('  ---   base.html already declares the components')

    tally = collections.Counter()
    for path in templates():
        if os.path.abspath(path) == os.path.abspath(BASE):
            continue
        p = plan_page(path)
        if p is None:
            continue
        if check_page(p, problems):
            planned.append(p)
            tally['rules'] += p['rules']
            tally['empty media'] += p['empties']
            tally['center tags'] += p['centers']

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    pages = [p for p in planned
             if p['rel'] not in ('base.html', 'Push-PendingChanges.ps1')]
    print('  %-34s %5s %6s %8s' % ('', 'rules', 'media', 'centers'))
    for p in pages:
        print('  %-34s %5d %6d %8d'
              % (p['rel'][:34], p['rules'], p['empties'], p['centers']))
    print('')
    print('  %d page(s); %d rule(s) removed, %d empty media block(s), '
          '%d center tag(s)'
          % (len(pages), tally['rules'], tally['empty media'],
             tally['center tags']))
    if b:
        print('  base.html gains the three components, once.')
    if g:
        print('  %s joins the gate.' % SUITE)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    if not planned:
        print('')
        print('  Nothing to do - everything is already in place.')
        return

    for p in planned:
        bak = p['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(p['raw'])
        write(p['path'], p['new'], p['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.'
          % SUFFIX)
    print('')
    print('  Next:  python test_heading_components.py')


if __name__ == '__main__':
    main()
