"""CO-2 - THE SAME BUG, IN THE OTHER LANGUAGE.

   CO-1 (3 Oct) moved the comment stripper into alv_tree and taught it the
   rule that had cost four rounds:

       `/*` IS NOT A COMMENT OPENER IN MARKUP.

   accept="image/*" puts one inside an attribute value, and blanking from
   there to the next `*/` anywhere in the file ate 3,362 characters of
   passport_management.html - ninety-four lines of the Add Passport form.
   alv_tree.code_only now strips the block syntax ONLY inside <style> and
   <script>, and a sentinel pins that shape.

   PUSH-PENDINGCHANGES.PS1 HAS ITS OWN STRIPPER AND IT NEVER LEARNED.
   NoComments, the function behind every `Code = $true` sentinel, carries
   the unconditional line:

       $t = [regex]::Replace($t, '/\\*.*?\\*/', '', $sl)

   Measured against alv_tree.code_only on the five templates that carry a
   `/*` outside a style block, in characters of real content destroyed by
   THIS STEP ALONE:

       passport_management.html       3,268
       edit_asset.html                1,088
       property_assets.html             776
       preview_imported_recipe.html       0
       my_profile.html                    0

   THE TWO ZEROES ARE THE PROOF THE MECHANISM IS THE ONE NAMED. Both
   carry the same attribute; neither has a later `*/` for the regex to
   run to, so there is nothing between the two points to destroy.

   AND THE FIRST BUILD OF THIS ROUND MEASURED 4,651 / 3,348 / 1,528 /
   1,222. Those numbers are the whole function's disagreement with
   code_only, and NoComments has a fourth step - blank any line beginning
   with `//` - which alv_tree deliberately does not have. Charging that
   step's losses to this one made preview_imported_recipe look like the
   worst page in the tree when this step costs it nothing. The suite now
   runs both models with that step switched off, so what is measured is
   what is being changed.

   NO SENTINEL IS WRONG TODAY, AND THAT IS THE WHOLE POINT. One
   `Code = $true` sentinel sits on a page this step damages -
   property_assets' `view-toggle-group` - and it is an `Absent = $true`
   row, which is the direction that hides a regression rather than
   inventing one: an "is it gone" check against a file with a hole in it
   passes for free. That string really is gone, inside a comment both
   strippers agree about, so the sentinel is right by luck rather than by
   construction. This round is written while that is still a measurement
   and not an incident.

   NO SCRIPTBLOCK, NO STRINGBUILDER. There is no PowerShell in this
   sandbox, so the replacement cannot be executed here - only its
   ALGORITHM can, and section 2 of the suite does exactly that by
   modelling it in Python and requiring it to agree with code_only on all
   150 templates. That makes the syntax the remaining risk, so the
   replacement uses only constructs this script already contains:
   [regex]::Matches (line 854), .Substring, [regex]::Replace and string
   concatenation. A MatchEvaluator scriptblock and a StringBuilder would
   both be new to the file, and a gate that cannot start is worse than
   one that reads a little too much.

   FILES: Push-PendingChanges.ps1.                [test_ps1_comment.py]
"""
import os
import sys

SUFFIX = '.bak_ps1comment'

PS1 = 'Push-PendingChanges.ps1'

OLD = ("    $t = [regex]::Replace($t, '/\\*.*?\\*/', '', $sl)\n")

NEW = (
    "    # CO-2, 5 Oct 2026 - `/*` IS NOT A COMMENT OPENER IN MARKUP, and\n"
    "    # the line that used to stand here said it was.  accept=\"image/*\"\n"
    "    # puts one inside an attribute value, and blanking from there to\n"
    "    # the next close anywhere in the file destroyed 3,268 characters\n"
    "    # of passport_management.html, 1,088 of edit_asset.html and 776\n"
    "    # of property_assets.html - the last of which carries a Code\n"
    "    # sentinel.  This is CO-1's rule, which alv_tree.code_only has\n"
    "    # had since 3 Oct, arriving in the other language: the block\n"
    "    # syntax is only a comment INSIDE <style> or <script>.\n"
    "    #\n"
    "    # Written with [regex]::Matches, .Substring and concatenation\n"
    "    # because this script already uses all three.  A MatchEvaluator\n"
    "    # scriptblock would be shorter and would be the first in the\n"
    "    # file, and a gate that will not start is worse than one that\n"
    "    # reads a little too much.\n"
    "    $out = ''\n"
    "    $last = 0\n"
    "    foreach ($m in [regex]::Matches($t, "
    "'(?is)<(style|script)\\b[^>]*>.*?</\\1>')) {\n"
    "        $out = $out + $t.Substring($last, $m.Index - $last)\n"
    "        $out = $out + [regex]::Replace($m.Value, '/\\*.*?\\*/', '', $sl)\n"
    "        $last = $m.Index + $m.Length\n"
    "    }\n"
    "    $t = $out + $t.Substring($last)\n")

MARK = '$out = $out + [regex]::Replace($m.Value'


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = os.path.join(os.getcwd(), PS1)
    if not os.path.isfile(path):
        raise SystemExit('CO-2: %s is not here' % PS1)
    text = read(path)

    if MARK in text:
        print('CO-2  edits : 0')
        print('CO-2  applied' if check else 'CO-2  ok')
        return 0

    n = text.count(OLD)
    if n != 1:
        raise SystemExit('CO-2: the unconditional block-comment line matched '
                         '%d times, expected 1. NoComments has changed since '
                         'this was measured - read it rather than let this '
                         'round guess.' % n)

    # THE FUNCTION MUST STILL BE THE ONE THIS ROUND READ. Three other
    # strippers live in it and none of them is this round's business.
    for needed in ("[regex]::Replace($Text, '<!--.*?-->', '', $sl)",
                   "'\\{#[^\\r\\n]*?#\\}'",
                   "$l.TrimStart().StartsWith('//')"):
        if needed not in text:
            raise SystemExit('CO-2: NoComments no longer contains %r - the '
                             'function has been rewritten' % needed)

    # AND THE EDIT MUST NOT MOVE THE BRACE BALANCE. A gate that will not
    # parse is the one failure this round could cause that nothing else
    # here would catch, and there is no PowerShell in this sandbox to
    # catch it with.
    #
    # NOT "the file balances" - IT DOES NOT, and the first build of this
    # round asserted that it did. This script carries brace characters
    # inside regex literals and inside the strings it searches for,
    # `\{#[^\r\n]*?#\}` among them, so the raw counts are 494 against 487
    # before anything is touched. What has to hold is that THIS EDIT
    # changes neither count, which is a claim about the edit rather than
    # about PowerShell.
    was = (text.count('{'), text.count('}'))
    text = text.replace(OLD, NEW, 1)
    now = (text.count('{'), text.count('}'))
    if now[0] - was[0] != now[1] - was[1]:
        raise SystemExit('CO-2: the edit changed the brace balance - open '
                         '%+d, close %+d' % (now[0] - was[0], now[1] - was[1]))

    if not check:
        backup(path)
        write(path, text)

    print('CO-2  edits : 1')
    print('CO-2  lines  : %+d' % (NEW.count('\n') - OLD.count('\n')))
    if check:
        print('CO-2  NOT APPLIED')
        return 1
    print('CO-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
