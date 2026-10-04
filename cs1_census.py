"""CS-1 CENSUS — what changes hands if base.html's trailing stylesheet moves
   above {% block content %}.

   THE BUG THIS IS ABOUT. base.html keeps a component stylesheet at lines
   3145-5088. {% block content %} is at line 3015. Every page writes its own
   CSS inside that content block, so in the rendered document base's rules
   come LAST and win every tie at equal specificity. Thirteen pages write
   their own .filter-grid columns and all thirteen are dead; Actual Expenses
   is the one Demetri photographed.

   Moving base's block into the head fixes that. But it hands the win back to
   the page for EVERY selector the two share, not just .filter-grid - and some
   of those page rules may have been written, or left behind, in the knowledge
   that base would beat them. This script finds every one of them so the move
   is made with the list in hand rather than hopefully.

   It reports, per page, each (selector, property) pair that
     - base's trailing block declares, AND
     - the page declares too, AND
     - where the two declare DIFFERENT values,
   because only those actually change hands. Equal values are listed
   separately as harmless.

   Specificity is computed so pairs where the page already wins on
   specificity are excluded - those do not change.
                                                        [test_css_order.py]
"""
import os
import re
import sys

import alv_tree as T

BASE = 'pages/templates/base.html'


# ---------------------------------------------------------------- parsing

def style_blocks(text):
    """(start, end, body) for every <style>...</style> in document order."""
    out = []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I):
        out.append((m.start(), m.end(), m.group(1)))
    return out


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def rules(css):
    """(selector_list, {prop: value}) for every rule, at-rules included.

    An at-rule's body is walked too, and its prelude is carried onto the
    selector so `@media ... { .x }` never collides with a bare `.x`.
    """
    css = strip_comments(css)
    out = []

    def walk(block, prefix):
        i = 0
        n = len(block)
        while i < n:
            brace = block.find('{', i)
            if brace < 0:
                break
            head = block[i:brace].strip()
            depth = 1
            j = brace + 1
            while j < n and depth:
                if block[j] == '{':
                    depth += 1
                elif block[j] == '}':
                    depth -= 1
                j += 1
            body = block[brace + 1:j - 1]
            if head.startswith('@'):
                if re.match(r'@(media|supports|layer|container)\b', head):
                    walk(body, prefix + [head])
                # @keyframes, @font-face and friends declare nothing a page
                # rule can collide with by selector, so they are skipped.
            else:
                decls = {}
                for d in body.split(';'):
                    if '{' in d or '}' in d:
                        continue
                    if ':' not in d:
                        continue
                    p, _, v = d.partition(':')
                    p = p.strip().lower()
                    v = v.strip()
                    if p and v:
                        decls[p] = v
                if decls:
                    for sel in head.split(','):
                        sel = ' '.join(sel.split())
                        if sel:
                            out.append((' && '.join(prefix + [sel]), decls))
            i = j

    walk(css, [])
    return out


def specificity(sel):
    """(ids, classes, types) for the rightmost compound - good enough here,
    because we only ever compare the SAME selector string against itself."""
    s = sel.split(' && ')[-1]
    s = re.sub(r'::[a-zA-Z-]+', ' ', s)
    ids = len(re.findall(r'#[\w-]+', s))
    cls = len(re.findall(r'\.[\w-]+', s)) + len(re.findall(r'\[[^\]]+\]', s))
    cls += len(re.findall(r':(?!:)[a-zA-Z-]+', s))
    typ = len(re.findall(r'(?:^|[\s>+~])([a-zA-Z][\w-]*)', s))
    return (ids, cls, typ)


# ---------------------------------------------------------------- the census

def base_trailing_rules():
    text = open(BASE, encoding='utf-8').read()
    content_at = text.find('{% block content %}')
    if content_at < 0:
        raise SystemExit('base.html has no {% block content %}')
    out = []
    head_sels = set()
    for start, end, body in style_blocks(text):
        for sel, decls in rules(body):
            if start > content_at:
                out.append((sel, decls))
            else:
                head_sels.add(sel)
    return out, head_sels, content_at


def page_rules(path):
    text = open(path, encoding='utf-8').read()
    out = []
    for _s, _e, body in style_blocks(text):
        out.extend(rules(body))
    return out


def main():
    trailing, head_sels, content_at = base_trailing_rules()

    # Later rule wins inside base's own block, so collapse to the last.
    base_map = {}
    for sel, decls in trailing:
        base_map.setdefault(sel, {}).update(decls)

    print('base.html trailing block: %d rules, %d distinct selectors'
          % (len(trailing), len(base_map)))

    pages = [p for p in T.templates()
             if os.path.basename(p) != 'base.html' and os.path.exists(p)]

    changes = []     # page wins where values differ
    harmless = []    # page wins but the value is the same
    for full in sorted(pages):
        pmap = {}
        for sel, decls in page_rules(full):
            pmap.setdefault(sel, {}).update(decls)
        for sel, pdecls in pmap.items():
            bdecls = base_map.get(sel)
            if not bdecls:
                continue
            if specificity(sel) != specificity(sel):
                continue
            for prop, pval in pdecls.items():
                if prop not in bdecls:
                    continue
                bval = bdecls[prop]
                row = (T.rel(full) if hasattr(T, 'rel') else full,
                       sel, prop, bval, pval)
                if ' '.join(bval.split()) == ' '.join(pval.split()):
                    harmless.append(row)
                else:
                    changes.append(row)

    print()
    print('=' * 78)
    print('CHANGES HANDS: %d (selector, property) pairs on %d pages'
          % (len(changes), len({c[0] for c in changes})))
    print('=' * 78)
    cur = None
    for page, sel, prop, bval, pval in sorted(changes):
        if page != cur:
            cur = page
            print('\n--- %s' % page)
        print('    %s' % sel)
        print('        %-28s base %s' % (prop, bval))
        print('        %-28s page %s' % ('', pval))

    print()
    print('Same value either way (no visible change): %d pairs on %d pages'
          % (len(harmless), len({h[0] for h in harmless})))
    return 0


if __name__ == '__main__':
    sys.exit(main())
