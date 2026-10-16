# -*- coding: utf-8 -*-
"""apply_deed_one_column.py - round TD-2, 16 Oct 2026.

ONE ACTION COLUMN, LIKE THE LEASE AGREEMENTS TABLE.

Demetri, looking at the two screens side by side after NV-1b shipped:

  "Should the Title Deed Table not match the Lease Agreement Table.
   There should only be one Action Column. No separate Title Deed
   column."

It should, and NV-1b left this half done. That round put the table on
`.alv-table`, gave it house pills and icon buttons, and took fifteen
rule openings out of its stylesheet - and left the two action columns
exactly as it found them.


THE LEASE AGREEMENTS TABLE ALREADY WRITES DOWN THE RULE
============================================================================
From `tenant_lease_agreement.html`, above its one action cell:

    Desktop actions: one cell. View is always drawn - as a disabled twin
    when there is nothing attached - so the column does not change width
    from row to row.

That is the whole of this round, applied to the page beside it.

    TENANT LEASE AGREEMENTS   Tenant | Property | Start | End | ACTIONS
    PROPERTY TITLE DEEDS      Property | Country | Status
                                         | TITLE DEED | ACTIONS

The deeds table splits ONE strip across TWO columns, and writes a `-`
where the other table draws a control.


AND THE DASH IS THE PART WORTH NAMING                            MEASURED
============================================================================
The deeds table had two `<span class="text-muted">-</span>` placeholders:
one where View would be when no deed is attached, one where
Delete/Upload would be when the reader cannot edit properties.

THE HOUSE PATTERN FOR "YOU CANNOT DO THIS" IS THE DISABLED TWIN, and it
is already on this page's own neighbours: the lease table draws
`icon-action-btn icon-disabled` in both places, and NV-1c drew the same
thing yesterday on the tenant invoice row, titled with the reason. A
dash is a third spelling of the same idea, and it reads as MISSING DATA
rather than as an action the reader does not have.

So both dashes become twins, and the column reads one width on every
row - which is the reason the lease table gives for drawing View even
when there is nothing to view.


THE COLUMN WIDTHS FOLLOW THE TABLE THIS ROUND IS MATCHING
============================================================================
    was   Property 35  Country 25  Status 15  Title Deed 15  Actions 10
    now   Property 40  Country 25  Status 20                 Actions 15

Actions is 15%, the same as the lease table's. The freed ten points go
to the two columns that actually hold text.

AND THE ACTION HEAD TAKES `desktop-action-cell cell-actions`, which is
how the lease table spells it: base centres both and `cell-actions`
stops the strip wrapping. `col-center` comes off it, because base
already centres a `.desktop-action-cell` head and two rules saying one
thing is how they come to disagree. Status keeps `col-center`.


THE PHONE IS NOT TOUCHED, AND THAT IS NOT AN OVERSIGHT
============================================================================
The two-column split was only ever a desktop shape. The phone bar
already draws ONE bar with View and Delete-or-Upload at `cols-2`, which
is what NV-1b gave it. Rendered at 320, 360, 390 and 414 before and
after: identical.


WHAT THIS ROUND DOES NOT DO
============================================================================
THE STATUS COLUMN STAYS, and it is now saying something the strip also
says: a disabled bookmark means no deed is attached, and so does
`Not Uploaded`. The lease agreements table has no Status column at all,
so if the two screens are to match properly that column is the
remaining difference. Raised with Demetri, not decided, not touched.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_deedonecol'
PAGE = 'title_deeds_management.html'
MODEL = 'tenant_lease_agreement.html'
ME = 'test_deed_one_column.py'
PATCHER = 'apply_deed_one_column.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
BH = 'test_bar_height.py'
DT = 'test_deed_table.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 88, 89
ALIAS_WAS, ALIAS_NOW = 87, 89
ALIAS_P_WAS, ALIAS_S_WAS = 43, 44
ALIAS_P_NOW, ALIAS_S_NOW = 44, 45

N_COLS_WAS, N_COLS_NOW = 5, 4
N_ROW_WAS, N_ROW_NOW = 114, 116

HEAD_WAS = """    <tr>
        <th style="width: 35%">Property Name</th>
        <th style="width: 25%">Country</th>
        <th class="col-center" style="width: 15%">Status</th>
        <th class="col-center" style="width: 15%">Title Deed</th>
        <th class="col-center" style="width: 10%">Actions</th>
    </tr>"""

HEAD_NOW = """    <tr>
        <th style="width: 40%">Property Name</th>
        <th style="width: 25%">Country</th>
        <th class="col-center" style="width: 20%">Status</th>
        <th class="desktop-action-cell cell-actions" style="width: 15%">Actions</th>
    </tr>"""

CELLS_WAS = """        <td data-label="Title Deed" class="desktop-action-cell">
            {% if property.prop_title_deed %}
                <span class="row-actions"><button type="button" class="icon-action-btn icon-document" title="View title deed" aria-label="View title deed" onclick="viewDocument('{{ property.prop_title_deed.url|escapejs }}', '{{ property.prop_title_deed.name|escapejs }}', '{{ property.prop_name|escapejs }}')">
                    <i class="fas fa-file-contract"></i>
                </button></span>
            {% else %}
                <span class="text-muted">-</span>
            {% endif %}
        </td>
        <td data-label="Action" class="desktop-action-cell">
            {% if perms.auth.can_edit_properties %}
                {% if property.prop_title_deed %}
                    <span class="row-actions"><button type="button" class="icon-action-btn icon-delete" title="Delete title deed" aria-label="Delete title deed" onclick="deleteDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-trash"></i>
                    </button></span>
                {% else %}
                    <span class="row-actions"><button type="button" class="icon-action-btn icon-upload" title="Upload title deed" aria-label="Upload title deed" onclick="uploadDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-upload"></i>
                    </button></span>
                {% endif %}
            {% else %}
                <span class="text-muted">-</span>
            {% endif %}
        </td>"""

CELLS_NOW = """        {# TD-2, 16 Oct 2026 - ONE ACTION CELL, like the lease agreements #}
        {# table beside it. Demetri: there should only be one Action #}
        {# Column, no separate Title Deed column. #}
        {# #}
        {# View is ALWAYS DRAWN - a disabled twin when there is nothing #}
        {# attached - so that the column that holds it #}
        {# does not change width from row to row. That is the reason #}
        {# tenant_lease_agreement.html gives for the same shape, in the #}
        {# same words, and it is why the two #}
        {# text-muted dashes are gone: the house pattern for an action #}
        {# the reader does not have is the twin, not a dash, which reads #}
        {# as missing DATA rather than as a missing ACTION. #}
        <td data-label="Actions" class="desktop-action-cell cell-actions">
            <span class="row-actions">
                {% if property.prop_title_deed %}
                    <button type="button" class="icon-action-btn icon-document" title="View title deed" aria-label="View title deed" onclick="viewDocument('{{ property.prop_title_deed.url|escapejs }}', '{{ property.prop_title_deed.name|escapejs }}', '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-file-contract"></i>
                    </button>
                {% else %}
                    <span class="icon-action-btn icon-disabled" title="No title deed uploaded">
                        <i class="fas fa-file-contract"></i>
                    </span>
                {% endif %}

                {% if perms.auth.can_edit_properties %}
                    {% if property.prop_title_deed %}
                        <button type="button" class="icon-action-btn icon-delete" title="Delete title deed" aria-label="Delete title deed" onclick="deleteDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    {% else %}
                        <button type="button" class="icon-action-btn icon-upload" title="Upload title deed" aria-label="Upload title deed" onclick="uploadDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                            <i class="fas fa-upload"></i>
                        </button>
                    {% endif %}
                {% else %}
                    <span class="icon-action-btn icon-disabled" title="No edit permission">
                        <i class="fas fa-upload"></i>
                    </span>
                {% endif %}
            </span>
        </td>"""

# --------------------------------------------- NV-1b's suite, re-pointed
DT_SHAPE_WAS = """ok(B_NOW.count('class="col-center"') == 3,
   'three heads ask for centring with base col-center - Status, Title '
   'Deed and Actions', B_NOW.count('class="col-center"'))"""

DT_SHAPE_NOW = """# TD-2, 16 Oct 2026 - ONE head asks now, because Demetri asked for one
# Action column and the Title Deed column went into it. The Actions head
# wears `desktop-action-cell cell-actions`, which base centres already,
# so col-center on it would be a second rule saying one thing.
ok(B_NOW.count('class="col-center"') == 1,
   'ONE head asks for centring with base col-center - Status. Actions is '
   'centred by base as a .desktop-action-cell, the way the lease '
   'agreements table spells it', B_NOW.count('class="col-center"'))"""

DT_RA_WAS = """ok(len(re.findall(r'class="row-actions"', B_NOW)) == 3,
   'three row-action strips - View, Delete and Upload',
   len(re.findall(r'class="row-actions"', B_NOW)))"""

DT_RA_NOW = """# TD-2, 16 Oct 2026 - ONE strip holds all of them now. Three strips was
# the two-column shape: one in the Title Deed cell and one in each arm
# of the Actions cell.
ok(len(re.findall(r'class="row-actions"', B_NOW)) == 1,
   'ONE row-action strip, holding View and Delete-or-Upload',
   len(re.findall(r'class="row-actions"', B_NOW)))"""

DT_TH_WAS = """ok(len(re.findall(r'<th\\b[^>]*width:\\s*\\d+%', B_NOW)) == 5,
   'and all five column widths are still inline on the heads - they are '
   "this table's, not the house's",
   len(re.findall(r'<th\\b[^>]*width:\\s*\\d+%', B_NOW)))"""

DT_TH_NOW = """ok(len(re.findall(r'<th\\b[^>]*width:\\s*\\d+%', B_NOW)) == 4,
   'and all FOUR column widths are still inline on the heads - they are '
   "this table's, not the house's. TD-2 merged the fifth into Actions "
   'and gave its ten points to the two columns holding text',
   len(re.findall(r'<th\\b[^>]*width:\\s*\\d+%', B_NOW)))"""

DT_ROW_WAS = """       '<td data-label="Title Deed" class="desktop-action-cell">'
       '<span class="row-actions"><button class="icon-action-btn '
       'icon-document"><i></i></button></span></td>'
       '<td data-label="Action" class="desktop-action-cell">@ACT</td>'"""

DT_ROW_NOW = """       '@ACTCELLS'"""

DT_HEADNOW_WAS = """THEAD_NOW = ('<tr><th style="width:35%">Property Name</th>'
             '<th style="width:25%">Country</th>'
             '<th class="col-center" style="width:15%">Status</th>'
             '<th class="col-center" style="width:15%">Title Deed</th>'
             '<th class="col-center" style="width:10%">Actions</th></tr>')"""

DT_HEADNOW_NOW = """# TD-2, 16 Oct 2026 - four heads, and Actions is centred by base as a
# .desktop-action-cell rather than by col-center, which is how the lease
# agreements table spells it.
THEAD_NOW = ('<tr><th style="width:40%">Property Name</th>'
             '<th style="width:25%">Country</th>'
             '<th class="col-center" style="width:20%">Status</th>'
             '<th class="desktop-action-cell cell-actions" '
             'style="width:15%">Actions</th></tr>')"""

DT_BEFORE_WAS = """              .replace('@ACT', '<button class="btn btn-sm btn-danger">'
                               '<i class="fas fa-trash"></i> Delete</button>')
              .replace('@BAR', ''))"""

DT_BEFORE_NOW = """              .replace('@ACTCELLS',
                       '<td data-label="Title Deed" '
                       'class="desktop-action-cell">'
                       '<span class="row-actions"><button '
                       'class="icon-action-btn icon-document">'
                       '<i></i></button></span></td>'
                       '<td data-label="Action" '
                       'class="desktop-action-cell">'
                       '<button class="btn btn-sm btn-danger">'
                       '<i class="fas fa-trash"></i> Delete</button></td>')
              .replace('@BAR', ''))"""

DT_AFTER_WAS = """              .replace('@ACT', '<span class="row-actions"><button '
                               'class="icon-action-btn icon-delete">'
                               '<i class="fas fa-trash"></i></button></span>')
              .replace('@BAR', ' cols-2'))"""

DT_AFTER_NOW = """              # TD-2, 16 Oct 2026 - ONE action cell now, holding the
              # whole strip, which is what Demetri asked for.
              .replace('@ACTCELLS',
                       '<td data-label="Actions" '
                       'class="desktop-action-cell cell-actions">'
                       '<span class="row-actions">'
                       '<button class="icon-action-btn icon-document">'
                       '<i></i></button>'
                       '<button class="icon-action-btn icon-delete">'
                       '<i class="fas fa-trash"></i></button>'
                       '</span></td>')
              .replace('@BAR', ' cols-2'))"""

DT_DESK_WAS = """            ok(a['align'][2:5] == b['align'][2:5]
               == ['center', 'center', 'center'],
               'desktop    and the three centred columns are still '
               'centred - col-center on the heads, and base centres the '
               'two action cells', (b['align'], a['align']))
            ok(a['shown'] == b['shown'] == 5,
               'desktop    five cells shown, before and after',
               (b['shown'], a['shown']))"""

DT_DESK_NOW = """            # TD-2, 16 Oct 2026 - THE COLUMN COUNT MOVED, so these two
            # ask about what each table actually has. Before: five
            # cells, three of them centred. After: four, with Status
            # centred by col-center and Actions centred by base as a
            # .desktop-action-cell. The claim is unchanged - every
            # column that should be centred is - and the numbers are
            # the ones each shape really holds.
            ok(a['align'][2:4] == ['center', 'center'],
               'desktop    Status and Actions read centred after the '
               'merge', a['align'])
            ok(b['align'][2:5] == ['center', 'center', 'center'],
               'desktop    CONTROL: and all three were centred before it',
               b['align'])
            ok(b['shown'] == 5 and a['shown'] == 4,
               'desktop    five cells shown before, FOUR after - the '
               'Title Deed column went into Actions',
               (b['shown'], a['shown']))"""

DT_DELTA_WAS = """ok(len(re.findall(r'class="icon-action-btn', B_NOW))
   - len(re.findall(r'class="icon-action-btn', B_WAS)) == 2,
   '  and the page gained exactly two icon-action-btns, no more',
   (len(re.findall(r'class="icon-action-btn', B_WAS)),
    len(re.findall(r'class="icon-action-btn', B_NOW))))"""

DT_DELTA_NOW = """# TD-2, 16 Oct 2026 - THIS ONE IS A DELTA, SO IT READS THE SNAPSHOT.
# It asks what NV-1b added, and B_NOW is the LIVE page - so every later
# round on this page is counted into NV-1b's delta. TD-2 added two
# disabled twins and the claim went from two to four without NV-1b
# doing anything. as_left_by walks ROUNDS forward from .bak_deedtable
# and returns the next round's backup, which IS the page as NV-1b left
# it, falling back to live when no later round exists.
_LEFT = code_only(as_left_by(PATH, SUFFIX, read)) if as_left_by else B_NOW
ok(len(re.findall(r'class="icon-action-btn', _LEFT))
   - len(re.findall(r'class="icon-action-btn', B_WAS)) == 2,
   '  and the page gained exactly two icon-action-btns, no more - asked '
   'of the page AS THIS ROUND LEFT IT, not of the live one',
   (len(re.findall(r'class="icon-action-btn', B_WAS)),
    len(re.findall(r'class="icon-action-btn', _LEFT))))"""

# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------- TD-2, 16 Oct 2026
    # Demetri, with the two screens side by side: should the Title Deed
    # table not match the Lease Agreement table - there should only be
    # one Action column. NV-1b put that table on .alv-table and left its
    # two action columns alone.
    @{ File = 'pages\\templates\\title_deeds_management.html'; Text = 'data-label="Actions" class="desktop-action-cell cell-actions"'; What = 'the title deeds table has ONE action column, like the lease agreements table' },
    @{ File = 'pages\\templates\\title_deeds_management.html'; Text = '<span class="text-muted">-</span>'; Absent = $true; Code = $true; What = 'and a disabled twin where it used to draw a dash - a dash reads as missing DATA, not as a missing action' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_customer_view.py'
)"""

SUITE_NOW = """    'test_customer_view.py',
    'test_deed_one_column.py'
)"""

TREE_WAS = """    'test_customer_view.py',
]"""

TREE_NOW = """    'test_customer_view.py',
    # TD-2, 16 Oct 2026 - the title deeds table reads like the lease
    # agreements table: one action column, View always drawn, and the
    # two text-muted dashes become disabled twins. Wide from birth.
    'test_deed_one_column.py',
]"""

ROUNDS_WAS = """    '.bak_custview',
]"""

ROUNDS_NOW = """    '.bak_custview',
    # TD-2, 16 Oct 2026 - title_deeds_management's Title Deed and Actions
    # columns become one, the way tenant_lease_agreement already draws
    # it. Finishes what NV-1b left: that round wore the house table and
    # kept the two-column split.
    '.bak_deedonecol',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('TD-2 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    if 'data-label="Actions" class="desktop-action-cell cell-actions"' \
            in code_only(read(page)):
        print('TD-2  already applied - the deeds table has one action '
              'column.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE MODEL IS READ, NOT REMEMBERED. Everything this round copies is
    # asserted against the table it is copying from.
    model = code_only(read(alv_tree.path_of(MODEL)))
    for need, what in (
            ('class="desktop-action-cell cell-actions"',
             'one action cell, carrying both house classes'),
            ('icon-action-btn icon-disabled', 'the disabled twin'),
            ('title="No edit permission"', 'the twin says why'),
            ('mobile-action-bar cols-2', 'and the phone draws one bar')):
        if need not in model:
            refuse('%s no longer shows %s (%s), so this round is copying '
                   'a table that has changed' % (MODEL, need, what))
    n_model_th = len(re.findall(r'<th\b[^>]*>', model))
    if 'class="desktop-action-cell cell-actions"' not in model:
        refuse('%s: the model head is not spelled as expected' % MODEL)

    # ---------------------------------------------------------------- 2
    s = read(page)
    s = swap(s, HEAD_WAS, HEAD_NOW, '%s (the heads)' % PAGE)
    s = swap(s, CELLS_WAS, CELLS_NOW, '%s (the two action cells)' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 3
    # GATES, every one asked of the CODE and most of them of the TABLE
    # TAG or the CELL rather than of the page - this round's own comment
    # spells `text-muted` and `Title Deed` in order to say they are gone.
    body = code_only(s)
    n_th = len(re.findall(r'<th\b', body))
    if n_th != N_COLS_NOW:
        refuse('%s: %d head(s), expected %d' % (PAGE, n_th, N_COLS_NOW))
    n_lab = len(re.findall(r'<td\b[^>]*data-label="', body))
    if n_lab != N_COLS_NOW:
        refuse('%s: %d labelled cell(s), expected %d - one per head'
               % (PAGE, n_lab, N_COLS_NOW))
    n_ra = len(re.findall(r'class="row-actions"', body))
    if n_ra != 1:
        refuse('%s: %d row-action strip(s), expected 1' % (PAGE, n_ra))
    for m in re.finditer(r'<(?:span|td)\b[^>]*class="([^"]*)"', body):
        if 'text-muted' in m.group(1).split():
            refuse('%s: a control still draws a dash instead of a '
                   'disabled twin - %r' % (PAGE, m.group(1)))
    if body.count('icon-action-btn icon-disabled') != 2:
        refuse('%s: %d disabled twin(s), expected 2 - one for View with '
               'nothing attached, one for a reader who cannot edit'
               % (PAGE, body.count('icon-action-btn icon-disabled')))
    # THE DESKTOP CELL IS ONE, AND THE PHONE BAR IS UNTOUCHED.
    n_dac = len(re.findall(r'<td\b[^>]*class="[^"]*desktop-action-cell',
                           body))
    if n_dac != 1:
        refuse('%s: %d desktop action cell(s), expected 1' % (PAGE, n_dac))
    if body.count('class="mobile-action-bar cols-2"') != 1:
        refuse('%s: the phone bar moved, and this round does not touch it'
               % PAGE)
    n_mb = len(re.findall(r'class="mobile-action-btn', body))
    if n_mb != 5:
        refuse('%s: %d phone control(s), expected the 5 NV-1b left'
               % (PAGE, n_mb))
    # WIDTHS STILL ADD TO 100.
    w = [int(x) for x in re.findall(r'<th\b[^>]*width:\s*(\d+)%', body)]
    if len(w) != N_COLS_NOW or sum(w) != 100:
        refuse('%s: the column widths are %s, which is %d%%'
               % (PAGE, w, sum(w)))
    if w[-1] != 15:
        refuse('%s: the Actions column is %d%%, and the table this round '
               'matches gives it 15%%' % (PAGE, w[-1]))
    # AND THE ORDER IS THE VOCABULARY'S.
    try:
        import alv_rowactions as RA
        if not RA.FAMILY['document'] < RA.FAMILY['upload'] \
                < RA.FAMILY['delete']:
            refuse('alv_rowactions no longer sorts document, upload, '
                   'delete in that order')
    except ImportError:
        refuse('alv_rowactions is not importable, and the strip order '
               'rests on it')

    # ---------------------------------------------------------------- 4
    # NV-1b'S SUITE, RE-POINTED. Four of its claims are about the shape
    # this round changes, and a round that falsifies a claim fixes it.
    p = os.path.join(root, DT)
    t = read(p)
    if 'TD-2, 16 Oct 2026' in t:
        refuse('%s already reads the one-column shape' % DT)
    t = swap(t, DT_SHAPE_WAS, DT_SHAPE_NOW, '%s (the centred heads)' % DT)
    t = swap(t, DT_RA_WAS, DT_RA_NOW, '%s (the strips)' % DT)
    t = swap(t, DT_TH_WAS, DT_TH_NOW, '%s (the widths)' % DT)
    t = swap(t, DT_ROW_WAS, DT_ROW_NOW, '%s (the fixture row)' % DT)
    t = swap(t, DT_HEADNOW_WAS, DT_HEADNOW_NOW, '%s (the fixture head)' % DT)
    t = swap(t, DT_BEFORE_WAS, DT_BEFORE_NOW, '%s (the before arm)' % DT)
    t = swap(t, DT_AFTER_WAS, DT_AFTER_NOW, '%s (the after arm)' % DT)
    t = swap(t, DT_DESK_WAS, DT_DESK_NOW, '%s (the desktop claims)' % DT)
    t = swap(t, DT_DELTA_WAS, DT_DELTA_NOW, '%s (the icon delta)' % DT)
    out[p] = t

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'TD-2, 16 Oct 2026 - this round own suite. The title '
                  'deeds table gets one action column, after Demetri put '
                  'it beside the lease agreements table and asked why it '
                  'has two.', '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'TD-2, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 5b
    # AND THE HEIGHT CENSUS, WHICH THIS ROUND MOVES WITHOUT ADDING A
    # CONTROL. test_bar_height counts the controls that carry a house
    # class, by where they sit. The two disabled twins are
    # .icon-action-btn spans inside a table row, so the table-row count
    # rises by two - and that is the point of a twin: it occupies the
    # place a control would. Found by the sweep, not by this file.
    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_BAR, N_ROW, N_MODAL = 267, %d, 95',
                  N_ROW_WAS, N_ROW_NOW,
                  'TD-2, 16 Oct 2026 - the two disabled twins. A twin is '
                  'an .icon-action-btn in a table row, so this census '
                  'counts it exactly as it counts the button it stands '
                  'in for - which is the whole idea.',
                  '%s (the table-row census)' % BH)

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('TD-2 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   %d column(s) -> %d; model head count %d'
              % (N_COLS_WAS, N_COLS_NOW, n_model_th))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('TD-2 applied.')
    print('   one action column, the way tenant_lease_agreement draws it')
    print('   View is ALWAYS drawn - a disabled twin when nothing is')
    print('         attached - so the column is one width on every row')
    print('   the two text-muted dashes become disabled twins: a dash')
    print('         reads as missing DATA, not as a missing ACTION')
    print('   widths 40 / 25 / 20 / 15, with Actions at 15%% like the')
    print('         table this round matches')
    print('   the phone bar is untouched - it already drew one bar')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
