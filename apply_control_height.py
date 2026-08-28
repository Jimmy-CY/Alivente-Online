#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Let every form control be as tall as the value it is showing.

Bootstrap 4.1.3 pins controls to a FIXED height -
`.form-control { height: calc(2.25rem + 2px) }`, 38px - and thirty-odd
templates add `padding: 10px 12px` or `10px 14px` on top without freeing it.
With border-box that leaves ~14px of content box for 14px text, so the value
is shaved off at the bottom.

The filter round already fixed this INSIDE `.alv-filter`. This round removes
the scope, because a control that cannot show its own value is broken
everywhere, not only in a filter panel.

MEASURED before writing this: 47 of 184 controls across 20 form templates
render shorter than their own content. Afterwards, none do. And that count is
a FLOOR - it was taken on Linux font metrics. Whether the clipping is visible
depends on the face: this was reported from a Windows machine on a dropdown
that measured "fine" here.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
BASE  = os.path.join(ROOT, 'pages', 'templates', 'base.html')
CHECK = '--check' in sys.argv

SCOPED = """.alv-filter select.form-control:not([size]):not([multiple]),
.alv-filter input.form-control,
.alv-filter textarea.form-control { height: auto; }"""

UNSCOPED = """/* WIDENED from `.alv-filter` to everywhere, %s. The rule below was
   added by the filter round for filter panels; the same defect is on every
   add/edit form in the system. Measured: 47 of 184 controls across 20 form
   templates were rendering shorter than their own content.

   The `:not()` pair is not decoration - Bootstrap's own selector carries it,
   so without matching that shape this rule is (0,1,1) against its (0,2,1)
   and loses, silently. That happened on the first attempt. */
select.form-control:not([size]):not([multiple]),
input.form-control,
textarea.form-control { height: auto; }"""


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def main():
    src = read(BASE)
    if 'WIDENED from `.alv-filter`' in src:
        print('  base.html            already widened - nothing to do')
        return
    n = src.count(SCOPED)
    if n != 1:
        sys.exit('! base.html: the scoped rule was found %d times, expected '
                 'exactly 1. Has the filter round been applied?' % n)

    out = src.replace(SCOPED, UNSCOPED % '27 Aug 2026')

    # ---- self-checks, before anything is written ------------------------
    def css(t):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))
    bad = []
    if css(out).count('{') != css(out).count('}'):
        bad.append('CSS braces do not balance')
    if '.alv-filter select.form-control' in out:
        bad.append('the scoped rule survived - there would be two of them')
    if out.count('select.form-control:not([size]):not([multiple])') != 1:
        bad.append('expected exactly one unscoped select rule')
    # the rule must still be INSIDE a <style>, not stranded in the body
    m = re.search(re.escape('input.form-control,\ntextarea.form-control'), out)
    if not m or css(out).find('textarea.form-control') < 0:
        bad.append('the rule did not land inside a <style> block')
    if len(re.findall(r'<style', out)) != len(re.findall(r'<style', src)):
        bad.append('the number of <style> blocks changed')
    if bad:
        sys.exit('! base.html self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  base.html            the height rule is no longer scoped to '
          '.alv-filter')
    if not CHECK:
        b = BASE + '.bak_ctlheight'
        if not os.path.exists(b):
            shutil.copy2(BASE, b)
        with open(BASE, 'w', encoding='utf-8') as f:
            f.write(out)
    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
