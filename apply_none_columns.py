# -*- coding: utf-8 -*-
"""SECTION N, ROUND N1 - A TEXT COLUMN STOPS HAVING TWO KINDS OF EMPTY

Demetri, on Suppliers: "When I add a new Supplier and I leave the email
address blank, the system inserts None in the field. Then if I edit that
supplier's telephone number and press Save, it tells me that email has to
have an @. Then if I clear the None from the field, it lets me save."

HE FOUND A DATA BUG, AND IT IS NOT A SUPPLIERS BUG.

    <input type="email" value="{{ sresults.supplier_email }}">

Django renders a NULL as the literal text `None`. The edit form comes up
with the word None sitting in the email box, you press Save, and `"None"`
is now REAL DATA in that column - at which point type="email" refuses it,
which is the message he saw. The Company Name column on his screenshot is
full of them.

THE SHAPE OF IT, MEASURED:

    227 inputs in 58 templates put a field straight into a value=
     43 textareas in 9 templates do the same
    641 places print a field into a cell or a label
    127 text columns across 28 models are null=True

TWO WAYS TO FIX IT, AND ONLY ONE OF THEM IS THE CAUSE. Adding a default
to 270 inputs treats the symptom, leaves the 641 displays still saying
None, and the next form anybody writes brings it back. The CAUSE is that
a text column is allowed to be NULL at all: Django's own documentation
says avoid null on a string field, because you end up with two possible
empty values and have to remember which is which everywhere.

    So null=True comes off all 127, existing NULLs and every literal
    "None" become empty text, and nothing renders None anywhere again.
    NOT ONE TEMPLATE IS EDITED.

WHY THIS IS SAFE, MEASURED RATHER THAN HOPED:

  - NOT ONE of the 127 is unique=True, so many rows sharing '' is fine.
    (A unique column full of NULLs cannot become a column full of empty
    strings - that was the first thing this round checked.)
  - ALL 127 already say blank=True, so no form starts demanding a value.
  - Of the 127, exactly TWO are ever tested for NULL anywhere in the
    codebase - supplier_country and invoice_number - and both already
    exclude the empty string as well, belt and braces, so neither one
    changes behaviour. Nothing uses `is None` on any of them.

WHAT THE MIGRATION DOES, IN THIS ORDER. The data first, while the column
still allows NULL; the schema second. It prints a line per column that
touched anything, so the damage is counted rather than guessed at.

REPORTED, NOT INVENTED. Six of the 127 carry choices and three carry a
default. A NULL in those columns was already outside the choices; it
becomes '' instead, which is also outside them and is at least not the
word None. Putting the default in instead would be inventing a value
nobody entered, so this round does not.

Backups: .bak_nonecols. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_nonecols'
CRLF = {}

MODELS = os.path.join('pages', 'models.py')
MIGDIR = os.path.join('pages', 'migrations')
MIG = '0095_none_columns.py'
PREV = '0094_alter_props_prop_include_in_occupancy'

KINDS = ('Char', 'Text', 'Email', 'URL')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('N1: %s is not a byte copy' % bak)


def declarations(text):
    """Every nullable text field, as (model, field, first_line, last_line).
    A declaration may span lines, so it is gathered by bracket depth
    rather than by looking at one line - six of them do."""
    lines = text.split('\n')
    out, cur, i = [], None, 0
    while i < len(lines):
        m = re.match(r'class (\w+)\(models\.Model\)', lines[i])
        if m:
            cur = m.group(1)
        f = re.match(r'(\s+)(\w+)\s*=\s*models\.(%s)Field\('
                     % '|'.join(KINDS), lines[i])
        if f and cur:
            j = i
            decl = lines[i]
            while decl.count('(') > decl.count(')') and j + 1 < len(lines):
                j += 1
                decl += '\n' + lines[j]
            if re.search(r'\bnull\s*=\s*True\b', decl):
                out.append((cur, f.group(2), i, j))
            i = j
        i += 1
    return out


def drop_null(decl):
    """null=True out of one declaration, and the comma that held it."""
    s = re.sub(r',\s*\n?\s*null\s*=\s*True\b', '', decl)
    if s == decl:
        s = re.sub(r'\bnull\s*=\s*True\s*,\s*', '', decl)
    if s == decl:
        s = re.sub(r'\bnull\s*=\s*True\b', '', decl)
    return s


def expression(decl):
    """The right-hand side on one line, for the migration. Any name that
    is not a literal is inlined from CHOICES below - a migration that
    referenced PROJECT_STATUS_CHOICES would raise NameError on deploy,
    which is a 500 on every screen rather than a layout bug."""
    rhs = decl.split('=', 1)[1].strip()
    rhs = ' '.join(rhs.split())
    rhs = re.sub(r'\(\s+', '(', rhs)
    rhs = re.sub(r'\s+\)', ')', rhs)
    rhs = re.sub(r',\s*\)', ')', rhs)
    for name, value in CHOICES.items():
        rhs = rhs.replace('choices=' + name, 'choices=' + value)
    return rhs


CHOICES = {}

# ==========================================================================
print('=' * 74)
print('SECTION N, ROUND N1 - A TEXT COLUMN STOPS HAVING TWO KINDS OF EMPTY%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

if not os.path.isfile(MODELS):
    raise SystemExit('N1: %s is not on disk' % MODELS)
t, raw = read(MODELS)
flat = t.replace('\r\n', '\n')

# The six choice constants, read from models.py rather than typed here.
for m in re.finditer(r'^\s*([A-Z][A-Z0-9_]*_CHOICES)\s*=\s*(\[.*?\])',
                     flat, re.S | re.M):
    CHOICES[m.group(1)] = ' '.join(m.group(2).split())
print('  %s' % MODELS)
print('     %d choice constant(s) read, to inline in the migration'
      % len(CHOICES))

decls = declarations(flat)
print('     %d nullable text column(s) across %d model(s)'
      % (len(decls), len(set(d[0] for d in decls))))

# ---- THE SAFETY CHECKS, BEFORE ANYTHING IS WRITTEN ----------------------
lines = flat.split('\n')
bad_unique, bad_blank, fields = [], [], []
for model, field, a, b in decls:
    decl = '\n'.join(lines[a:b + 1])
    if re.search(r'\bunique\s*=\s*True\b', decl):
        bad_unique.append('%s.%s' % (model, field))
    if not re.search(r'\bblank\s*=\s*True\b', decl):
        bad_blank.append('%s.%s' % (model, field))
    fields.append((model, field))
# A UNIQUE COLUMN FULL OF NULLS CANNOT BECOME A COLUMN FULL OF ''.
if bad_unique:
    raise SystemExit('N1: %d of them are unique=True and cannot take a '
                     'shared empty value: %s' % (len(bad_unique), bad_unique))
# AND NO FORM MAY START DEMANDING A VALUE.
if bad_blank:
    raise SystemExit('N1: %d of them are not blank=True, so dropping null '
                     'would make a form require them: %s'
                     % (len(bad_blank), bad_blank))
print('     none unique, all blank=True - the two things that would make')
print('     this unsafe, and neither is true')

if not decls:
    print('     already done - no text column is nullable')
else:
    # ---- models.py --------------------------------------------------
    new = list(lines)
    for model, field, a, b in reversed(decls):
        decl = '\n'.join(lines[a:b + 1])
        cut = drop_null(decl)
        if 'null=True' in cut.replace(' ', ''):
            raise SystemExit('N1: %s.%s still says null=True after the cut:'
                             '\n%s' % (model, field, cut))
        new[a:b + 1] = cut.split('\n')
    out = '\n'.join(new)
    # NOTHING ELSE MOVED. Only null=True may leave, and nothing may
    # arrive: a patcher that reflowed a declaration would be rewriting
    # code it was only asked to read.
    before = re.sub(r'\s+', '', flat)
    after = re.sub(r'\s+', '', out)
    if after != before.replace('null=True,', '').replace(',null=True', '') \
            .replace('null=True', ''):
        # fall back to a token-level comparison, which is the real claim
        strip = lambda s: re.sub(r'\bnull=True\b,?|,\s*\bnull=True\b', '',
                                 re.sub(r'\s+', '', s))
        if strip(flat) != strip(out):
            raise SystemExit('N1: models.py changed by more than null=True')
    left = len(re.findall(r'\bnull\s*=\s*True\b', out))
    print('     null=True removed from %d column(s); %d left on non-text '
          'fields, which keep it' % (len(decls), left))

    # ---- the migration ----------------------------------------------
    rows, alters = [], []
    for model, field, a, b in decls:
        decl = drop_null('\n'.join(lines[a:b + 1]))
        rows.append("    ('%s', '%s')," % (model, field))
        alters.append(
            "        migrations.AlterField(\n"
            "            model_name='%s',\n"
            "            name='%s',\n"
            "            field=%s,\n"
            "        )," % (model.lower(), field, expression(decl)))
    for a_ in alters:
        for name in CHOICES:
            if name in a_:
                raise SystemExit('N1: the migration still names %s, which '
                                 'does not exist inside a migration' % name)

    body = '''# -*- coding: utf-8 -*-
"""ROUND N1 - a text column stops having two kinds of empty.

Demetri found this on Suppliers: leave the email blank, and the edit form
comes back with the word None in the box, because Django renders a NULL
as the text "None". Press Save and "None" is real data - and then
type="email" refuses it.

The cause is that a text column may be NULL at all. Django's own
documentation says not to do that on a string field: you end up with two
possible empty values and have to remember which is which in every
template, every filter and every form.

So: %d text columns across %d models lose null=True. THE DATA RUNS FIRST,
while the column still allows NULL - every NULL and every value that is
exactly the string "None" becomes ''. Then the schema follows.

The forward pass prints one line per column it actually touched, so the
damage is counted rather than guessed at. It is safe to run twice: the
second time it finds nothing and says so.

REVERSING restores null=True on the columns. It does NOT put the NULLs
back, because which rows were NULL and which were already '' is exactly
the distinction this round exists to destroy, and inventing it again
would be worse than leaving them empty. See test_none_columns.py.
"""
from django.db import migrations, models


COLUMNS = [
%s
]


def empty_the_nones(apps, schema_editor):
    """Every NULL, and every literal "None", becomes ''."""
    total_null = total_word = 0
    for model_name, field in COLUMNS:
        model = apps.get_model('pages', model_name)
        n_null = model.objects.filter(**{field + '__isnull': True}).update(
            **{field: ''})
        n_word = model.objects.filter(**{field: 'None'}).update(**{field: ''})
        if n_null or n_word:
            print('    %%-30s %%5d NULL  %%5d "None"'
                  %% (model_name + '.' + field, n_null, n_word))
        total_null += n_null
        total_word += n_word
    print('    %%d NULL and %%d literal "None" value(s) emptied across %%d '
          'column(s)' %% (total_null, total_word, len(COLUMNS)))


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '%s'),
    ]

    operations = [
        # THE DATA FIRST. Emptying a NULL after the column has been made
        # NOT NULL is not possible - the ALTER is what would fail.
        migrations.RunPython(empty_the_nones, migrations.RunPython.noop),
%s
    ]
''' % (len(decls), len(set(d[0] for d in decls)), '\n'.join(rows), PREV,
       '\n'.join(alters))

    mig_path = os.path.join(MIGDIR, MIG)
    import ast
    try:
        ast.parse(body)
    except SyntaxError as e:
        raise SystemExit('N1: the generated migration does not parse: %s' % e)
    # EVERY COLUMN IS IN BOTH HALVES.
    if body.count('migrations.AlterField(') != len(decls):
        raise SystemExit('N1: %d AlterField(s) for %d column(s)'
                         % (body.count('migrations.AlterField('), len(decls)))
    # THE TWO HALVES NAME THE SAME COLUMNS. Compared as lists rather
    # than counted out of the rendered text: the first version of this
    # gate counted lines in `body` with a regex and was defeated by the
    # inlined choices, which is a gate measuring its own formatting.
    in_rows = [tuple(re.findall(r"'([^']+)'", r)) for r in rows]
    # `name='` also matches inside `model_name='`, which made the first
    # version of this read the model twice and call it a mismatch.
    in_alt = [(re.search(r"model_name='([^']+)'", a).group(1),
               re.search(r"\n\s+name='([^']+)'", a).group(1))
              for a in alters]
    if [(m.lower(), f) for m, f in in_rows] != in_alt:
        raise SystemExit('N1: the COLUMNS list and the AlterFields name '
                         'different columns')
    if len(in_rows) != len(decls):
        raise SystemExit('N1: %d row(s) for %d declaration(s)'
                         % (len(in_rows), len(decls)))
    print('  %s' % os.path.join(MIGDIR, MIG))
    print('     the data first, then %d AlterField(s)' % len(decls))

    if not CHECK:
        back_up(MODELS, raw)
        write(MODELS, out)
        if not os.path.isfile(mig_path):
            with open(mig_path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(body)
        print('     written')

# ---- what is reported, not invented -------------------------------------
print('  reported, not invented')
withch = [(m, f) for m, f, a, b in decls
          if 'choices=' in '\n'.join(lines[a:b + 1])]
withdf = [(m, f) for m, f, a, b in decls
          if re.search(r'\bdefault\s*=', '\n'.join(lines[a:b + 1]))]
print('     %d column(s) carry choices, %d carry a default. A NULL in those'
      % (len(withch), len(withdf)))
print('     was already outside the choices; it becomes empty, not the')
print('     default, because a default would be a value nobody entered.')
for m, f in withch:
    print('        choices  %s.%s' % (m, f))

print('-' * 74)
print('  one migration, no template edited, and None stops being a value.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
