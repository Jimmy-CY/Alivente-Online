"""apply_detail_property - the Property module's detail and report screens.

    python apply_detail_property.py --check
    python apply_detail_property.py

WHAT
----
Three screens onto the standard, plus two corrections to base.html that this
round is the first to need:

  property_report.html   the two asset tables, and every status badge
  property_assets.html   the asset table, the summary card, the group cards
  asset_detail.html      four coloured card headers, the maintenance table,
                         and its Invoice + Action columns collapsed into one

TWO CORRECTIONS TO base.html
----------------------------
1. `.alv-card { overflow: hidden }` was wrong, and I wrote it. An ancestor
   with `overflow: hidden` becomes the scroll container, so a sticky heading
   inside a card has nothing to stick to. Measured: scroll 600px and the
   heading is 542px above the viewport - gone. With `overflow: clip` it pins
   at 0. This is the identical fault we fixed on `.table-container` a round
   earlier; it was latent only because no page used `.alv-card` yet.

2. A fifth tag tone. The maintenance type has five named values plus a
   fallback - scheduled, repair, inspection, cleaning, service - and four
   tones cannot carry five categories without claiming two are related.

WHAT IS DELIBERATELY NOT DONE
-----------------------------
The report's own layout - `.report-container`, `.property-card`,
`.section-title`, `.detail-row` - is left alone. It is already quiet, it
prints, and converting it would be churn for no visible gain. This round
touches tables, badges and coloured bars only.

Idempotent. Backs up each file to .bak_detailprop.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

FILES = ('base.html', 'property_report.html', 'property_assets.html',
         'asset_detail.html')

src = {}
meta = {}
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

CHANGES = []
NOTES = []


def sub(name, label, old, new, mark):
    """Replace exactly once in `name`, or explain why not.

    `mark` may be a string OR a callable taking the text. It has to be able
    to be a callable: the first draft of this file used the phrase
    "clip, NOT hidden" as the marker for the .alv-card fix, and the polish
    round had already written that exact phrase into the .table-container
    comment three hundred lines above. The patcher reported the change as
    already applied and quietly did nothing. Prose is not a mechanism -
    third time on this project.
    """
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
    """Replace exactly `count` times - for markup repeated per column."""
    if (mark(src[name]) if callable(mark) else (mark in src[name])):
        CHANGES.append((name, 'skip', label))
        return
    n = src[name].count(old)
    if n != count:
        sys.exit('! %s / %s: the anchor matched %d times (expected %d)\n'
                 '  anchor: %s' % (name, label, n, count, old.strip()[:90]))
    src[name] = src[name].replace(old, new)
    CHANGES.append((name, 'apply', '%s (x%d)' % (label, count)))


# =====================================================================
# 0.  base.html - the two corrections
# =====================================================================
sub('base.html', 'a card no longer traps the sticky heading inside it',
    """      .alv-card {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        border-radius: 6px;
        margin-bottom: 20px;
        overflow: hidden;
      }""",
    """      .alv-card {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        border-radius: 6px;
        margin-bottom: 20px;
        /* clip, NOT hidden. An ancestor with overflow:hidden becomes the
           scroll container, so a sticky heading inside a card has nothing
           to stick to - measured 542px above the viewport after a 600px
           scroll. clip rounds the corners without that side effect. The
           same fault, and the same fix, as .table-container. */
        overflow: clip;
      }""",
    lambda t: re.search(r'\.alv-card \{[^}]*overflow:\s*clip', t) is not None)

sub('base.html', 'a fifth tag tone, for the fifth maintenance type',
    """      .alv-tag-slate { color: #55606b; background: #eef1f3; border-color: #e0e5e9; }""",
    """      .alv-tag-slate { color: #55606b; background: #eef1f3; border-color: #e0e5e9; }
      .alv-tag-plum  { color: #6b4a72; background: #f3edf5; border-color: #e5dae8; }""",
    '.alv-tag-plum')

# The dot says "this is one of a set of categories". A toneless tag is not
# a category - it is a count, on a card header - and a leading dot in front
# of a bare number reads as a bullet. So the dot moves onto the tones.
sub('base.html', '  and the dot moves onto the tones, so a count has none',
    """      .alv-tag::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        opacity: .55;
        flex: none;
      }""",
    """      .alv-tag-sky::before,
      .alv-tag-moss::before,
      .alv-tag-clay::before,
      .alv-tag-slate::before,
      .alv-tag-plum::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        opacity: .55;
        flex: none;
      }""",
    # The MECHANISM - do the tones carry the dot - not the absence of the
    # old selector. `'.alv-tag::before' not in t` was wrong twice over: the
    # print block legitimately carries `.alv-tag::before { opacity: 1 }`, so
    # the string never disappears, and the marker therefore reported "not
    # done" forever. First run: correct. Every run after: 0 matches and a
    # hard exit. I added this substitution AFTER checking idempotence and
    # did not re-check. That is the actual lesson.
    lambda t: '.alv-tag-sky::before' in t)


# =====================================================================
# 1.  property_report.html
# =====================================================================
R = 'property_report.html'

sub(R, 'the category table joins the standard',
    '<table class="categories-table">',
    '<table class="table alv-table categories-table">',
    'alv-table categories-table')

sub(R, 'the asset table joins the standard',
    '<table class="assets-table">',
    '<table class="table alv-table assets-table">',
    'alv-table assets-table')

sub(R, '  Count is a number, so it gets tabular figures',
    '<th class="count-col">Count</th>',
    '<th class="count-col num">Count</th>',
    'count-col num')

sub(R, '  and so does its cell',
    '<td data-label="Count" class="count-col"><strong>{{ cat.count }}</strong></td>',
    '<td data-label="Count" class="count-col num"><strong>{{ cat.count }}</strong></td>',
    'data-label="Count" class="count-col num"')

# Centring was a table-wide habit; the standard left-aligns text and
# right-aligns numbers, so these three centring hooks go.
sub(R, '  Purchase Date stops being centred',
    '<th class="text-center">Purchase Date</th>',
    '<th>Purchase Date</th>',
    '<th>Purchase Date</th>')
sub(R, '  and Warranty with it',
    '<th class="text-center">Warranty</th>',
    '<th>Warranty</th>',
    '<th>Warranty</th>')
sub(R, '  and the cells that followed them',
    '<td data-label="Purchase Date" class="text-center">'
    '{{ asset.purchase_date|date:"Y-m-d" }}</td>',
    '<td data-label="Purchase Date">'
    '{{ asset.purchase_date|date:"Y-m-d" }}</td>',
    '<td data-label="Purchase Date">{{ asset')
sub(R, '  including the warranty cell',
    '<td data-label="Warranty" class="text-center">',
    '<td data-label="Warranty">',
    '<td data-label="Warranty">')

sub(R, '  Category becomes a tag, not bare text',
    '<td data-label="Category">{{ asset.subcategory.name }}</td>',
    '<td data-label="Category">'
    '<span class="alv-tag alv-tag-slate">{{ asset.subcategory.name }}</span></td>',
    'alv-tag alv-tag-slate">{{ asset.subcategory.name')

sub(R, 'Status becomes a pill',
    """<span class="badge {% if property.prop_status == 'Active' %}badge-success{% else %}badge-secondary{% endif %}">""",
    """<span class="alv-pill {% if property.prop_status == 'Active' %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">""",
    "alv-pill-good{% else %}alv-pill-neutral{% endif %}")

sub(R, '  and so does Available for Rent',
    """<span class="badge {% if property.prop_available_for_rent == 'Yes' %}badge-available{% else %}badge-not-available{% endif %}">""",
    """<span class="alv-pill {% if property.prop_available_for_rent == 'Yes' %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">""",
    'alv-pill-good{% else %}alv-pill-neutral{% endif %}">\n                            {{ property.prop_available_for_rent')

sub(R, '  the active-warranty count',
    '<span class="badge badge-success">{{ active_warranties }}</span>',
    '<span class="alv-pill alv-pill-good">{{ active_warranties }}</span>',
    'alv-pill-good">{{ active_warranties }}')

# Amber, not red. An expired warranty has lapsed and is actionable; it is
# not a failure. The inline style went with it - a colour typed into an
# attribute cannot be restyled from base.html, and prints as a background
# the print dialog will drop.
sub(R, '  and the expired one turns amber, losing its inline style',
    '<span class="badge" style="background-color: #dc3545; color: white;">'
    '{{ expired_warranties }}</span>',
    '<span class="alv-pill alv-pill-attn">{{ expired_warranties }}</span>',
    'alv-pill-attn">{{ expired_warranties }}')

sub(R, '  the warranty column reads as pills',
    """                                            <span class="warranty-active">✓ Active</span><br>
                                            <small>{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>
                                        {% else %}
                                            <span class="warranty-expired">✗ Expired</span><br>
                                            <small>{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>""",
    """                                            <span class="alv-pill alv-pill-good">Active</span><br>
                                            <small class="muted-small">{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>
                                        {% else %}
                                            <span class="alv-pill alv-pill-attn">Expired</span><br>
                                            <small class="muted-small">{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>""",
    'alv-pill alv-pill-attn">Expired')


# =====================================================================
# 2.  property_assets.html
# =====================================================================
A = 'property_assets.html'

sub(A, 'the summary panel becomes a card',
    """<div class="card mb-4 summary-card">
    <div class="card-body">
        <h5 class="card-title"><i class="fas fa-info-circle"></i> Asset Summary</h5>
        <div class="summary-grid">""",
    """<div class="alv-card">
    <div class="alv-card-head">
        <i class="fas fa-info-circle"></i>
        <span class="alv-card-title">Asset Summary</span>
    </div>
    <div class="alv-card-body">
        <div class="summary-grid">""",
    '<div class="alv-card">\n    <div class="alv-card-head">\n        <i class="fas fa-info-circle">')

sub(A, '  each group becomes a card, its count an aside',
    """<div class="category-section mb-4">
        <h4 class="category-header">
            <i class="fas {% if group_by == 'room' %}fa-door-open{% else %}fa-tag{% endif %}"></i> <span class="category-name">{{ group_name }}</span>
            <span class="badge badge-secondary category-count">{{ asset_list|length }}</span>
        </h4>

        <table class="asset-table">""",
    """<div class="alv-card">
        <div class="alv-card-head">
            <i class="fas {% if group_by == 'room' %}fa-door-open{% else %}fa-tag{% endif %}"></i>
            <span class="alv-card-title category-name">{{ group_name }}</span>
            <span class="alv-card-aside alv-tag">{{ asset_list|length }}</span>
        </div>

        <div class="table-container">
        <table class="table alv-table asset-table">""",
    'alv-card-aside alv-tag">{{ asset_list|length }}')

sub(A, '  and the table closes inside it',
    """        </table>
    </div>
    {% endfor %}""",
    """        </table>
        </div>
    </div>
    {% endfor %}""",
    '</table>\n        </div>\n    </div>')

sub(A, '  Warranty Expiry stops being centred',
    '<th class="text-center">Warranty Expiry</th>',
    '<th>Warranty Expiry</th>',
    '<th>Warranty Expiry</th>')

sub(A, '  and its cell with it',
    '<td data-label="Warranty Expiry" class="text-center">',
    '<td data-label="Warranty Expiry">',
    '<td data-label="Warranty Expiry">')

sub(A, '  Subcategory becomes a tag',
    '<td data-label="Subcategory">{{ asset.subcategory.name }}</td>',
    '<td data-label="Subcategory">'
    '<span class="alv-tag alv-tag-slate">{{ asset.subcategory.name }}</span></td>',
    'alv-tag alv-tag-slate">{{ asset.subcategory.name')

sub(A, '  and the warranty column reads as pills',
    """                                <span class="warranty-active">✓ Active</span><br>
                                <small>{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>
                            {% else %}
                                <span class="warranty-expired">✗ Expired</span><br>
                                <small>{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>""",
    """                                <span class="alv-pill alv-pill-good">Active</span><br>
                                <small class="text-muted">{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>
                            {% else %}
                                <span class="alv-pill alv-pill-attn">Expired</span><br>
                                <small class="text-muted">{{ asset.warranty_expiry_date|date:"Y-m-d" }}</small>""",
    'alv-pill alv-pill-attn">Expired')


# =====================================================================
# 3.  asset_detail.html
# =====================================================================
D = 'asset_detail.html'

sub(D, 'the asset card leads, and loses its blue bar',
    """<div class="card mb-4 detail-card">
    <div class="card-header bg-primary text-white">
        <h4 class="mb-0">""",
    """<div class="alv-card alv-card-lead">
    <div class="alv-card-head">
        <h4 class="alv-card-title mb-0">""",
    '<div class="alv-card alv-card-lead">')

sub(D, '  and its body follows suit',
    """            {{ asset.name }}
        </h4>
    </div>
    <div class="card-body">
        <div class="detail-groups">""",
    """            {{ asset.name }}
        </h4>
    </div>
    <div class="alv-card-body">
        <div class="detail-groups">""",
    '<div class="alv-card-body">\n        <div class="detail-groups">')

sub(D, '  the photo thumb gets a visible border again',
    """.asset-header-thumb {
    width: 60px;
    height: 60px;
    border-radius: 8px;
    object-fit: cover;
    border: 2px solid rgba(255, 255, 255, 0.4);""",
    """/* The border was white, for a blue bar that no longer exists. On the
   card surface a white border is invisible. */
.asset-header-thumb {
    width: 60px;
    height: 60px;
    border-radius: 8px;
    object-fit: cover;
    border: 2px solid var(--alv-line);""",
    'border: 2px solid var(--alv-line);')

sub(D, '  and its hover border too',
    'border-color: rgba(255, 255, 255, 0.8);',
    'border-color: var(--alv-ink-faint);',
    'border-color: var(--alv-ink-faint);')

sub(D, 'the Photos card loses its teal bar; the count becomes a tag',
    """<div class="card mb-4 detail-card">
    <div class="card-header bg-info text-white">
        <h5 class="mb-0">
            <i class="fas fa-camera"></i> Photos
            <span class="badge badge-light text-info">{{ photos|length }}</span>
        </h5>
    </div>
    <div class="card-body">
        <div class="photo-grid">""",
    """<div class="alv-card">
    <div class="alv-card-head">
        <i class="fas fa-camera"></i>
        <span class="alv-card-title">Photos</span>
        <span class="alv-card-aside alv-tag">{{ photos|length }}</span>
    </div>
    <div class="alv-card-body">
        <div class="photo-grid">""",
    'alv-card-aside alv-tag">{{ photos|length }}')

# The bar was green whether the warranty was live or dead - bg-success on
# the header, and the real answer in a badge beside it. Now the header is
# quiet and the pill is the only thing that changes.
sub(D, 'the Warranty card stops being green regardless of the warranty',
    """<div class="card mb-4 detail-card">
    <div class="card-header {% if asset.is_warranty_active %}bg-success{% else %}bg-secondary{% endif %} text-white">
        <h5 class="mb-0">
            <i class="fas fa-shield-alt"></i> Warranty Information
            {% if asset.is_warranty_active %}
                <span class="badge badge-light text-success">ACTIVE</span>
            {% else %}
                <span class="badge badge-light text-danger">EXPIRED / N/A</span>
            {% endif %}
        </h5>
    </div>
    <div class="card-body">
        <div class="warranty-grid">""",
    """<div class="alv-card">
    <div class="alv-card-head">
        <i class="fas fa-shield-alt"></i>
        <span class="alv-card-title">Warranty Information</span>
        {% if asset.is_warranty_active %}
            <span class="alv-card-aside alv-pill alv-pill-good">Active</span>
        {% else %}
            <span class="alv-card-aside alv-pill alv-pill-attn">Expired / N/A</span>
        {% endif %}
    </div>
    <div class="alv-card-body">
        <div class="warranty-grid">""",
    'alv-pill alv-pill-attn">Expired / N/A')

# Days Remaining stays plain text. The first draft made it a green pill and
# the render showed why that is wrong: it sits beside "48 months" and
# "March 13, 2030", two plain values, and a duration is not a status. The
# pill in the card header already says the warranty is live.
sub(D, '  Days Remaining keeps the good ink, but stays text',
    """                        <span class="text-success">{{ asset.warranty_days_remaining }} days</span>""",
    """                        <span style="color: var(--alv-good)">{{ asset.warranty_days_remaining }} days</span>""",
    'color: var(--alv-good)">{{ asset.warranty_days_remaining }}')

sub(D, 'the Maintenance card loses its teal bar',
    """<div class="card mb-4 detail-card">
    <div class="card-header bg-info text-white">
        <div class="card-header-row">
            <h5 class="mb-0">
                <i class="fas fa-wrench"></i> Maintenance History
            </h5>
            {% if perms.auth.can_edit_properties %}
                <button type="button" class="btn btn-sm btn-light" data-toggle="modal" data-target="#addMaintenanceModal">
                    <i class="fas fa-plus"></i> Add Record
                </button>
            {% else %}
                <span class="btn btn-sm btn-light disabled-btn">
                    <i class="fas fa-plus"></i> Add Record
                </span>
            {% endif %}
        </div>
    </div>
    <div class="card-body">""",
    """<div class="alv-card">
    <div class="alv-card-head">
        <i class="fas fa-wrench"></i>
        <span class="alv-card-title">Maintenance History</span>
        <span class="alv-card-aside">
            {% if perms.auth.can_edit_properties %}
                <button type="button" class="btn btn-sm btn-info" data-toggle="modal" data-target="#addMaintenanceModal">
                    <i class="fas fa-plus"></i> Add Record
                </button>
            {% else %}
                <span class="btn btn-sm btn-info disabled-btn">
                    <i class="fas fa-plus"></i> Add Record
                </span>
            {% endif %}
        </span>
    </div>
    <div class="alv-card-body">""",
    '<span class="alv-card-aside">\n            {% if perms.auth.can_edit_properties %}')

sub(D, '  the maintenance table joins the standard',
    '<table class="maintenance-table">',
    '<div class="table-container">\n            '
    '<table class="table alv-table maintenance-table">',
    'alv-table maintenance-table')

# Invoice and Action were two columns holding three buttons between them.
# The standard has one Actions column, and every conditional below is moved
# with its button rather than re-derived.
sub(D, '  Invoice and Action collapse into ONE Actions column',
    """                        <th class="text-right">Cost (&euro;)</th>
                        <th class="text-center">Invoice</th>
                        <th class="text-center">Action</th>""",
    """                        <th class="num">Cost (&euro;)</th>
                        <th class="cell-actions">Actions</th>""",
    '<th class="cell-actions">Actions</th>')

sub(D, '  Type becomes a tag, on five tones and a plain fallback',
    """                            <span class="badge badge-{% if record.maintenance_type == 'scheduled' %}info{% elif record.maintenance_type == 'repair' %}warning{% elif record.maintenance_type == 'inspection' %}primary{% elif record.maintenance_type == 'cleaning' %}success{% elif record.maintenance_type == 'service' %}dark{% else %}secondary{% endif %}">""",
    """                            <span class="alv-tag {% if record.maintenance_type == 'scheduled' %}alv-tag-sky{% elif record.maintenance_type == 'repair' %}alv-tag-clay{% elif record.maintenance_type == 'inspection' %}alv-tag-slate{% elif record.maintenance_type == 'cleaning' %}alv-tag-moss{% elif record.maintenance_type == 'service' %}alv-tag-plum{% endif %}">""",
    "alv-tag-plum{% endif %}")

sub(D, '  Cost right-aligns as a number',
    '<td data-label="Cost" class="text-right cost-cell">',
    '<td data-label="Cost" class="num cost-cell">',
    'class="num cost-cell"')

sub(D, '  and the three buttons move into one cell, conditionals intact',
    """                        <td data-label="Invoice" class="text-center">
                            {% if record.invoice %}
                                <button type="button" class="btn btn-sm btn-info" onclick="viewInvoice('{{ record.invoice.url }}', '{{ record.invoice.name }}')">
                                    <i class="fas fa-file-invoice"></i>
                                </button>
                            {% else %}
                                <span class="text-muted">&mdash;</span>
                            {% endif %}
                        </td>
                        <td data-label="Action" class="text-center action-cell">
                            {% if perms.auth.can_edit_properties %}
                                <button type="button" class="btn btn-sm btn-warning"
                                    onclick="openEditMaintenance(""",
    """                        <td data-label="Actions" class="desktop-action-cell cell-actions">
                          <span class="row-actions">
                            {% if record.invoice %}
                                <button type="button" class="icon-action-btn icon-view" title="View invoice" onclick="viewInvoice('{{ record.invoice.url }}', '{{ record.invoice.name }}')">
                                    <i class="fas fa-file-invoice"></i>
                                </button>
                            {% else %}
                                <span class="icon-action-btn icon-disabled" title="No invoice attached">
                                    <i class="fas fa-file-invoice"></i>
                                </span>
                            {% endif %}
                            {% if perms.auth.can_edit_properties %}
                                <button type="button" class="icon-action-btn icon-edit" title="Edit record"
                                    onclick="openEditMaintenance(""",
    'class="desktop-action-cell cell-actions">')

print('')
print('  ... asset_detail action buttons: closing the collapsed cell')

# The tail of that cell: the remaining three buttons and the two </td>s that
# are now one.
_tail_old = """                                <button type="button" class="btn btn-sm btn-danger" onclick="confirmDeleteMaintenance({{ record.id }})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            {% else %}
                                <button type="button" class="btn btn-sm btn-warning disabled-btn">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-danger disabled-btn">"""
_tail_new = """                                <button type="button" class="icon-action-btn icon-delete" title="Delete record" onclick="confirmDeleteMaintenance({{ record.id }})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            {% else %}
                                <span class="icon-action-btn icon-disabled" title="No permission">
                                    <i class="fas fa-edit"></i>
                                </span>
                                <span class="icon-action-btn icon-disabled" title="No permission">"""
sub(D, '  delete and the disabled twins keep their places',
    _tail_old, _tail_new, 'icon-action-btn icon-delete" title="Delete record"')


# =====================================================================
# 4.  delete the CSS base.html now owns
# =====================================================================
DEAD = {
    R: ('.categories-table', '.assets-table', '.badge', '.badge-success',
        '.badge-secondary', '.badge-info', '.badge-light', '.badge-available',
        '.badge-not-available', '.warranty-active', '.warranty-expired'),
    A: ('.asset-table', '.badge', '.warranty-active', '.warranty-expired',
        '.summary-card', '.category-section', '.category-header'),
    D: ('.maintenance-table', '.detail-card', '.card-header-row'),
}


def strip_css_comments(s):
    """A captured selector carries any comment above its rule. `/* MOBILE */
    @media (...)` does not start with '@', so an at-rule preceded by a
    comment reads as an ordinary rule and its whole body goes unscanned.
    That has happened on this project once already."""
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


def is_dead(one_selector, dead):
    """One comma-part. Dead if its FIRST class is a dead page component - which
    covers `.assets-table td[data-label="..."]` - or every class it names is."""
    s = strip_css_comments(one_selector)
    if not s or s.startswith('@'):
        return False
    parts = re.findall(r'\.[A-Za-z0-9_-]+', s)
    if not parts:
        return False
    # Anything naming a standard class is code THIS round added, never a
    # leftover. Without this the mobile opt-out below - which is written as
    # `.categories-table.alv-table` - was deleted on the second run, because
    # its first class is a dead page component. The rule vanished, its empty
    # @media wrapper did not, and the patcher stopped being idempotent.
    if any(p.startswith('.alv-') for p in parts):
        return False
    return parts[0] in dead or all(p in dead for p in parts)


removed = {}
for name in (R, A, D):
    m = re.search(r'(<style[^>]*>)(.*?)(</style>)', src[name], re.S | re.I)
    if not m:
        sys.exit('! %s has no <style> block' % name)
    css = m.group(2)
    dead = DEAD[name]
    already = re.search(r'<table[^>]*\balv-table\b', src[name]) is not None
    cuts = []

    def scan(block, offset):
        for at, selector, s0, s1, b0, b1 in top_rules(block, offset):
            if at:
                scan(css[b0 + 1:b1], b0 + 1)
                continue
            sels = [x for x in strip_css_comments(selector).split(',')
                    if x.strip()]
            flags = [is_dead(x, dead) for x in sels]
            if sels and all(flags):
                cuts.append((s0, s1))
            elif any(flags):
                NOTES.append('%s: kept a rule mixing owned and page-specific '
                             'selectors - %s'
                             % (name, ' '.join(selector.split())[:70]))

    scan(css, 0)
    if not cuts:
        # Nothing left to cut. On a converted file that is the correct
        # second-run answer; on a fresh one it means the dead set is wrong,
        # which must be loud. Idempotence is decided by the MECHANISM - is
        # the markup already on the standard - not by a marker comment. The
        # first draft guarded on a comment it never wrote, and a second run
        # errored instead of skipping.
        if already:
            CHANGES.append((name, 'skip', 'CSS deletion'))
            removed[name] = 0
            continue
        sys.exit('! %s: nothing matched for deletion - the dead set is wrong'
                 % name)
    out = []
    prev = 0
    for s0, s1 in sorted(cuts):
        out.append(css[prev:s0])
        prev = s1
    out.append(css[prev:])
    new_css = ''.join(out)
    new_css = re.sub(r'\n{3,}', '\n\n', new_css)
    removed[name] = len(cuts)
    src[name] = (src[name][:m.start()] + m.group(1) + new_css + m.group(3)
                 + src[name][m.end():])
    CHANGES.append((name, 'apply', 'deleted %d rules base.html now owns'
                    % len(cuts)))

# The count table was going to opt OUT of the mobile card conversion - a
# two-column table is narrow enough for a phone, and three rows becoming
# three cards seemed like a loss. It is not worth it. base.html carries
# `.alv-table tbody td:first-child { display: block }` at specificity
# (0,2,2), which beats a `.categories-table.alv-table td` override, and
# `.alv-table td` sets padding, border and text-align with !important on
# top. Winning that argument takes eight lines of counter-override per
# page, forever. Three cards read fine. The house pattern wins.

# =====================================================================
# 5.  verify before writing anything
# =====================================================================
problems = []

for name in FILES:
    t = src[name]
    for i, line in enumerate(t.split('\n'), 1):
        if '{#' in line and '#}' not in line:
            problems.append('%s: unclosed {# comment at line %d - Django '
                            'renders it as visible text' % (name, i))
    if t.count('{%') != t.count('%}'):
        problems.append('%s: Django tags do not balance (%d open, %d close)'
                        % (name, t.count('{%'), t.count('%}')))
    for m in re.finditer(r'(<style[^>]*>)(.*?)(</style>)', t, re.S | re.I):
        body = re.sub(r'/\*.*?\*/', ' ', m.group(2), flags=re.S)
        if body.count('{') != body.count('}'):
            problems.append('%s: CSS braces do not balance (%d/%d)'
                            % (name, body.count('{'), body.count('}')))

# Structure: every table we touched must open and close cleanly.
for name, n_tables in ((R, 2), (A, 1), (D, 1)):
    t = src[name]
    if t.count('<table') != t.count('</table>'):
        problems.append('%s: %d <table> vs %d </table>'
                        % (name, t.count('<table'), t.count('</table>')))
    # Count the TAGS, not every mention of the class - property_report also
    # names .alv-table six times in its mobile opt-out rule.
    n_on = len(re.findall(r'<table[^>]*\balv-table\b', t))
    if n_on != n_tables:
        problems.append('%s: expected %d tables on the standard, found %d'
                        % (name, n_tables, n_on))

# div balance, ignoring Django branches: count raw tags. A collapsed cell
# that lost a </td> shows up here.
for name in (R, A, D):
    t = re.sub(r'<!--.*?-->', '', src[name], flags=re.S)
    for tag in ('td', 'tr', 'thead', 'tbody'):
        o = len(re.findall(r'<%s[\s>]' % tag, t))
        c = len(re.findall(r'</%s>' % tag, t))
        if o != c:
            problems.append('%s: <%s> %d vs </%s> %d' % (name, tag, o, tag, c))

# Nothing may still reference a class we deleted.
for name, gone in ((R, ('warranty-active', 'warranty-expired',
                        'badge-available', 'badge-not-available')),
                   (A, ('warranty-active', 'warranty-expired')),
                   (D, ('card-header-row', 'bg-primary', 'bg-success'))):
    for g in gone:
        if g in src[name]:
            problems.append('%s: still mentions %s after its CSS went'
                            % (name, g))

# The collapse must not have dropped a permission conditional.
if src[D].count('perms.auth.can_edit_properties') < 3:
    problems.append('asset_detail.html: a permission conditional went missing '
                    '(%d left, expected >= 3)'
                    % src[D].count('perms.auth.can_edit_properties'))
if 'openEditMaintenance(' not in src[D] or \
        'confirmDeleteMaintenance(' not in src[D]:
    problems.append('asset_detail.html: an action handler was lost')

# base.html corrections
if 'overflow: hidden' in src['base.html'][
        src['base.html'].find('.alv-card {'):
        src['base.html'].find('.alv-card {') + 400]:
    problems.append('base.html: .alv-card still clips with hidden')
if '.alv-tag-plum' not in src['base.html']:
    problems.append('base.html: the fifth tag tone is missing')

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
cur = None
for name, kind, label in CHANGES:
    if name != cur:
        print('  %s' % name)
        cur = name
    print('    %-7s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
for n in NOTES:
    print('    NOTE    %s' % n)
print('')
for name in (R, A, D):
    before = len(open(os.path.join(TPL, name), encoding=meta[name][0],
                      errors='replace').read().replace('\r\n', '\n')
                 .split('\n'))
    after = len(src[name].split('\n'))
    print('  %-24s %4d -> %4d lines  (%d removed, %d%%)'
          % (name, before, after, before - after,
             round(100.0 * (before - after) / before)))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

for name in FILES:
    p = os.path.join(TPL, name)
    bak = p + '.bak_detailprop'
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    enc, nl = meta[name]
    with io.open(p, 'w', encoding=enc, newline='') as fh:
        fh.write(src[name].replace('\n', nl) if nl != '\n' else src[name])
    print('  wrote pages/templates/%s' % name)
print('')
print('Now run:  python test_detail_property.py')
