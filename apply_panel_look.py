"""apply_panel_look.py - the panel takes the Customer Invoice look, which
   is what was asked for and what the last round got backwards.

    python apply_panel_look.py --check     survey, write nothing
    python apply_panel_look.py             apply

Run from the repo root, after apply_form_components.py.

WHAT WENT WRONG, SAID PLAINLY

  The brief was: ONE set of standards, all of it in base, and the system
  should look like the New Customer Invoice screen.

  I surveyed 115 templates, found that 22 of 23 panels were flat white and
  that the gradient was one page, and recommended white. The count was
  correct and the recommendation was wrong. A majority tells you what the
  system DOES; it cannot tell you what it SHOULD DO, and that had already
  been decided - by the person who asked for the model page's look. The
  same mistake in the other direction was avoided on 9 Sep, when the label
  standard went against a 338-to-207 majority on purpose.

  Show-FormComponents.py prints "the majority is evidence, not the answer"
  at the bottom of its own output. I wrote that line and then recommended
  the majority anyway.

WHY THE REPAIR IS ONE RULE, AND WHY THAT IS THE POINT

  Before the last round, changing the panel meant editing 23 pages and
  hoping. The round pulled the panel out of all of them and into base, so
  the look is now ONE DECLARATION. Getting it wrong cost a rewrite of six
  lines rather than a rewrite of the system, which is the whole argument
  for having components at all.

WHAT CHANGES

  .form-card takes the model screen's own values:

      background     the wash, surface -> a deeper surface stop
      box-shadow     0 4px 12px rgba(0,0,0,0.06)   softer and wider
      padding        20px 24px                     tighter than 28px
      margin-bottom  22px

  The border stays 1px in the line token - the model page's #dee2e6 and
  base's token differ by less than the eye resolves, and the token is
  what keeps the panel in the palette.

  A NEW TOKEN, --alv-surface-deep, carries the gradient's far stop. The
  model page wrote #e9ecef as a literal. A gradient built from two tokens
  can be restated once; a gradient built from a literal has to be found
  again.

  NOTHING ELSE MOVES. The control, the field, the label and the help text
  were already the model screen's values and are not touched. This is the
  panel only.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
SUFFIX = '.bak_panellook'

TOKEN_ANCHOR = '--alv-surface:'
TOKEN_LINE = ('    --alv-surface-deep: #e9ecef;'
              '  /* the far stop of the panel wash */\n')

OLD = """.form-card {
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}"""

NEW = """.form-card {
    background: linear-gradient(135deg,
                var(--alv-surface) 0%, var(--alv-surface-deep) 100%);
    border: 1px solid var(--alv-line);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 22px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}"""

# The block's prose argued for white from a count. It has to change with
# the rule, or base carries a comment that contradicts the declaration
# underneath it - which is worse than no comment at all.
DOC_OLD = """   THE PANEL IS WHITE. 22 of the 23 panels in the system are; the gradient
   was one page, and a grey wash behind every form is a great deal more
   grey than behind one. The 12px radius and the shadow are the majority
   and the model page both."""

DOC_NEW = """   THE PANEL CARRIES THE MODEL SCREEN'S WASH, and the first version of
   this block did not. 22 of the 23 panels in the system were flat white
   and the gradient was one page, so the count said white and the count
   was answering the wrong question. The brief was never "what do most
   pages do"; it was "make the system look like New Customer Invoice".
   A majority is evidence about the present, not an argument about the
   standard - the label standard went against a 338-to-207 majority on
   purpose for exactly this reason.

   It cost six lines to correct because the panel lives here now. Before
   this block existed it would have cost 23 pages."""


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def main():
    check_only = '--check' in sys.argv
    if not os.path.exists(BASE):
        print('! %s not found - run from the repo root' % BASE)
        sys.exit(1)

    text, nl, raw = read(BASE)
    new = text
    steps, problems = [], []

    if '--alv-surface-deep' in text:
        steps.append('the wash token is already there')
    else:
        i = new.find(TOKEN_ANCHOR)
        if i < 0:
            problems.append('%s not found, so the token has nowhere to go'
                            % TOKEN_ANCHOR)
        else:
            j = new.find('\n', i) + 1
            new = new[:j] + TOKEN_LINE + new[j:]
            steps.append('base gains --alv-surface-deep')

    if NEW in new:
        steps.append('the panel already carries the wash')
    elif new.count(OLD) == 1:
        new = new.replace(OLD, NEW, 1)
        steps.append('the panel takes the model screen\'s wash, shadow, '
                     'padding and gap')
    else:
        problems.append('the .form-card rule is not in the shape this round '
                        'expects (found %d match(es)) - has it been edited by '
                        'hand?' % new.count(OLD))

    if DOC_NEW in new:
        steps.append('the block already explains why')
    elif new.count(DOC_OLD) == 1:
        new = new.replace(DOC_OLD, DOC_NEW, 1)
        steps.append('and the comment above it stops arguing for white')
    else:
        problems.append('the block\'s comment is not in the shape this round '
                        'expects (found %d match(es))' % new.count(DOC_OLD))

    # SELF-CHECK. Everything outside this one rule and its comment must be
    # byte-identical, and the rule must reference only tokens.
    if not problems:
        # FROM THE BLOCK, not from the top of the file. Section 3.6 names
        # .form-section-title in its prose, so a search from position zero
        # lands hundreds of lines above the stylesheet and drags the token
        # edit into the comparison - which then reports the change this
        # round deliberately made as something that should not have moved.
        a = text.find('/* ===== ALV FORM v1')
        na = new.find('/* ===== ALV FORM v1')
        b = text.find('.form-section-title {', a) if a >= 0 else -1
        nb = new.find('.form-section-title {', na) if na >= 0 else -1
        if a < 0 or na < 0 or b < 0 or nb < 0:
            problems.append('the ALV FORM v1 block is not there to change')
        else:
            tail_same = text[b:] == new[nb:]
            if not tail_same:
                problems.append('something after the panel rule changed')
            m = re.search(r'\.form-card \{(.*?)\}', new, re.S)
            if not m:
                problems.append('the panel rule did not come out parseable')
            else:
                body = m.group(1)
                for lit in re.findall(r'#[0-9a-fA-F]{3,6}', body):
                    problems.append('the panel rule still carries the literal '
                                    '%s instead of a token' % lit)
                if 'linear-gradient' not in body:
                    problems.append('the panel rule has no wash')

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    for s in steps:
        print('  %s' % s)
    print('')
    print('  The panel now reads:')
    for line in NEW.split('\n'):
        print('    %s' % line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    bak = BASE + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'wb') as f:
            f.write(raw)
    write(BASE, new, nl)
    print('')
    print('  Written. Backup is base.html%s and is never overwritten.' % SUFFIX)
    print('')
    print('  Next:  python test_form_components.py')


if __name__ == '__main__':
    main()
