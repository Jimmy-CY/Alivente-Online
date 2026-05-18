"""
Help system views.

Two views support the user-facing Help page and the downloadable User
Manual PDF.

Functions
---------
- help_page            : Renders the main Help page - an accordion of
                         all help modules grouped by top-level menu
                         section, with client-side search filtering.
                         Permission-filtered to what the logged-in user
                         can access (superusers see everything; others
                         see only modules whose declared `permission`
                         they hold; modules with no declared permission
                         are always visible).
- generate_user_manual : Two-pass xhtml2pdf pipeline plus a ReportLab
                         footer overlay produces a personalised User
                         Manual PDF. Served inline so the JS preview
                         modal can render it in an iframe; a custom
                         X-Manual-Filename header carries the
                         user-facing filename for the Download button.

Notes
-----
Extracted from the legacy pages/views/main.py - these functions had
been misplaced in the recipe-management section by historical
organisation drift; they are not recipe-related.

Cleanups applied during the extraction:
  - Consolidated the `_user_can_see_module(user, module)` helper that
    was duplicated (identical logic) inside both views into a single
    module-level private helper.
  - Hoisted inline imports (help_renderer, io, reportlab, pypdf) from
    inside the functions to module-level imports.
"""

import io

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from xhtml2pdf import pisa

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from ..services.help_renderer import get_all_modules, get_all_modules_grouped


def _user_can_see_module(user, module):
    """
    True if the given user is allowed to see the given help module.

    Superusers see everything. Modules with no `permission` declared
    are always visible. Otherwise the user must hold the named auth
    permission (e.g. 'auth.can_access_properties').
    """
    if user.is_superuser:
        return True
    perm = module.get('permission', '')
    if not perm:
        return True  # no permission declared = always visible
    # Permissions live under the 'auth' app (e.g. auth.can_access_properties)
    return user.has_perm(f'auth.{perm}')


@login_required
def help_page(request):
    """
    The main Help page. Renders an accordion of all 32 help modules
    grouped by top-level menu section, with client-side search filtering.
    All 32 help modals are rendered in-page so clicks open them instantly.

    Modules are filtered against the logged-in user's permissions:
    superusers see everything; other users see only modules whose
    data-module-permission they hold (modules with no permission declared
    are always visible).
    """
    grouped = get_all_modules_grouped()

    # Prune modules the user is not allowed to see. Empty sub-sections and
    # empty groups are removed so no empty cards are rendered.
    filtered_grouped = []
    for group in grouped:
        direct = [m for m in group['direct_modules']
                  if _user_can_see_module(request.user, m)]

        subsections = []
        for sub in group['subsections']:
            visible_mods = [m for m in sub['modules']
                            if _user_can_see_module(request.user, m)]
            if visible_mods:
                subsections.append({
                    'name': sub['name'],
                    'parent_module_slug': sub['parent_module_slug'],
                    'parent_module_name': sub['parent_module_name'],
                    'modules': visible_mods,
                })

        if direct or subsections:
            filtered_grouped.append({
                'name': group['name'],
                'direct_modules': direct,
                'subsections': subsections,
            })

    grouped = filtered_grouped

    # Build a flat set of visible slugs, used to render only the modals the
    # user can see (and to drive the JS search index implicitly via template).
    visible_slugs = set()
    for group in grouped:
        for m in group['direct_modules']:
            visible_slugs.add(m['slug'])
        for sub in group['subsections']:
            for m in sub['modules']:
                visible_slugs.add(m['slug'])

    # Enrich every visible module with a lowercased, HTML-stripped 'search_text'
    # blob used by the client-side filter. Safe: mutation is idempotent and
    # no other template reads this key.
    def _build_search_text(module):
        parts = [module.get('name', ''), module.get('subtitle', '')]
        for tab in module.get('tabs', []):
            parts.append(tab.get('name', ''))
            parts.append(strip_tags(tab.get('content_html', '')))
        text = ' '.join(p for p in parts if p).lower()
        return ' '.join(text.split())  # collapse whitespace runs

    for group in grouped:
        for m in group['direct_modules']:
            if 'search_text' not in m:
                m['search_text'] = _build_search_text(m)
        for sub in group['subsections']:
            for m in sub['modules']:
                if 'search_text' not in m:
                    m['search_text'] = _build_search_text(m)

    # Flat list, pruned to only modules the user can see, used to render modals
    all_modules_flat = [m for m in get_all_modules() if m['slug'] in visible_slugs]

    # Icon for each top-level group (used on the accordion header)
    group_icons = {
        'Property Operations':  'fa-building',
        'Financial Management': 'fa-chart-line',
        'Administration':       'fa-cogs',
        'Personal':             'fa-user-circle',
        'Notifications':        'fa-bell',
        'My Profile':           'fa-user',
    }

    # Total module count per group, for the header badge.
    # Also attach each sub-section to its parent module (so the template can
    # render nested children inline under the parent), and collect leftover
    # "orphan" sub-sections that have no parent module.
    for group in grouped:
        total = len(group['direct_modules'])

        # Index direct modules by slug for quick lookup
        direct_by_slug = {m['slug']: m for m in group['direct_modules']}

        # Initialise per-module nested_subs lists
        for m in group['direct_modules']:
            m['nested_subs'] = []

        # Partition sub-sections: nested (attached to a parent module) vs orphan
        orphan_subs = []
        for sub in group['subsections']:
            total += len(sub['modules'])
            parent_slug = sub.get('parent_module_slug')
            if parent_slug and parent_slug in direct_by_slug:
                direct_by_slug[parent_slug]['nested_subs'].append(sub)
            else:
                orphan_subs.append(sub)

        group['orphan_subsections'] = orphan_subs
        group['total_count'] = total
        group['icon'] = group_icons.get(group['name'], 'fa-folder')

    context = {
        'grouped': grouped,
        'all_modules_flat': all_modules_flat,
        'total_module_count': sum(g['total_count'] for g in grouped),
    }
    return render(request, 'help_page.html', context)


@login_required
@require_POST
def generate_user_manual(request):
    """
    Generates a personalised User Manual PDF.

    Architecture - the long story short, we had to fight xhtml2pdf on
    several fronts to get this reliable. The shape of the pipeline:

      STEP 1 - Build the hierarchical chapter tree from the user's
               checkbox-tree selection, permission-filtered.

      STEP 2 - FIRST xhtml2pdf PASS: render the body (cover + TOC +
               chapters) using plain @page margins (NO @frame). The
               TOC page is rendered with EMPTY page-number columns
               because we don't know them yet. We only need this pass
               so pypdf can read the PDF outlines (from h1/h2/h3
               -pdf-outline directives) and discover each heading's
               page number.

      STEP 3 - Inject the discovered page numbers back into the
               context tree. Each chapter/nested module now has a
               `page_num` attribute.

      STEP 4 - SECOND xhtml2pdf PASS: re-render the body with the
               TOC now showing real page numbers.

      STEP 5 - Build a footer overlay PDF with ReportLab canvas
               ("Page X of Y" on every page except the cover).

      STEP 6 - pypdf merges the overlay onto every body page.

    Returns the final PDF as `inline` so the JS preview modal can
    display it in an iframe. A custom `X-Manual-Filename` header
    carries the user-facing filename for the Download button.

    Why two render passes? xhtml2pdf's built-in <pdf:toc/> macro
    triggers ReportLab's multiBuild, which combined with other
    features amplifies pagination bugs in rich content. Running
    xhtml2pdf twice ourselves is slower but far more predictable.
    """
    # -------- Parse selections ------------------------------------
    selected_modules = set(request.POST.getlist('selected_modules'))
    selected_tabs = request.POST.getlist('selected_tabs')

    tabs_by_module = {}
    for combined in selected_tabs:
        if '::' not in combined:
            continue
        mod_slug, tab_slug = combined.split('::', 1)
        tabs_by_module.setdefault(mod_slug, set()).add(tab_slug)

    # -------- Permission re-check ---------------------------------
    all_modules_by_slug = {m['slug']: m for m in get_all_modules()}
    accessible_slugs = {
        slug for slug, m in all_modules_by_slug.items()
        if _user_can_see_module(request.user, m)
    }

    # -------- Filter each module to selected tabs only ------------
    def _filter_module_for_pdf(module):
        """Return a shallow-copied module with only selected tabs, or None."""
        if module['slug'] not in selected_modules:
            return None
        if module['slug'] not in accessible_slugs:
            return None
        wanted = tabs_by_module.get(module['slug'], set())
        kept_tabs = [t for t in module.get('tabs', []) if t['slug'] in wanted]
        if not kept_tabs:
            return None
        return {
            'slug':     module['slug'],
            'name':     module['name'],
            'icon':     module.get('icon', ''),
            'subtitle': module.get('subtitle', ''),
            'group':    module.get('group', ''),
            'category': module.get('category', ''),
            'tabs':     kept_tabs,
        }

    # -------- Build the hierarchical pdf_groups structure ---------
    grouped = get_all_modules_grouped()

    for group in grouped:
        direct_by_slug = {m['slug']: m for m in group['direct_modules']}
        for m in group['direct_modules']:
            m['nested_subs'] = []
        orphan_subs = []
        for sub in group['subsections']:
            parent_slug = sub.get('parent_module_slug')
            if parent_slug and parent_slug in direct_by_slug:
                direct_by_slug[parent_slug]['nested_subs'].append(sub)
            else:
                orphan_subs.append(sub)
        group['orphan_subsections'] = orphan_subs

    pdf_groups = []
    total_modules_included = 0

    for group in grouped:
        pdf_chapters = []

        for m in group['direct_modules']:
            filtered = _filter_module_for_pdf(m)
            nested_chapters = []
            for sub in m.get('nested_subs', []):
                sub_mods = []
                for nm in sub['modules']:
                    nf = _filter_module_for_pdf(nm)
                    if nf:
                        sub_mods.append(nf)
                if sub_mods:
                    nested_chapters.append({
                        'name': sub['name'],
                        'modules': sub_mods,
                    })
            if filtered or nested_chapters:
                pdf_chapters.append({
                    'module': filtered,
                    'nested': nested_chapters,
                })
                if filtered:
                    total_modules_included += 1
                total_modules_included += sum(len(n['modules']) for n in nested_chapters)

        orphan_sub_chapters = []
        for sub in group.get('orphan_subsections', []):
            sub_mods = []
            for om in sub['modules']:
                of = _filter_module_for_pdf(om)
                if of:
                    sub_mods.append(of)
            if sub_mods:
                orphan_sub_chapters.append({
                    'name': sub['name'],
                    'modules': sub_mods,
                })
                total_modules_included += len(sub_mods)

        if pdf_chapters or orphan_sub_chapters:
            pdf_groups.append({
                'name':                group['name'],
                'icon':                group.get('icon', ''),
                'chapters':            pdf_chapters,
                'orphan_sub_chapters': orphan_sub_chapters,
            })

    # -------- Guard: nothing to print -----------------------------
    if total_modules_included == 0:
        return HttpResponse(
            'No modules with selected tabs were found. Please select at least one tab.',
            status=400, content_type='text/plain'
        )

    # -------- Cover page module list ------------------------------
    cover_module_list = []
    for group in pdf_groups:
        for ch in group['chapters']:
            if ch['module']:
                cover_module_list.append(ch['module']['name'])
            for n in ch['nested']:
                for nm in n['modules']:
                    cover_module_list.append(f"\u2022 {nm['name']}")
        for osc in group['orphan_sub_chapters']:
            for om in osc['modules']:
                cover_module_list.append(om['name'])

    full_name = request.user.get_full_name() or request.user.username

    context = {
        'pdf_groups':        pdf_groups,
        'generated_on':      timezone.now(),
        'user_full_name':    full_name,
        'user_username':     request.user.username,
        'total_modules':     total_modules_included,
        'cover_module_list': cover_module_list,
    }

    # -------- Helper: render body to an in-memory PDF buffer -------
    def _render_body(ctx):
        html = render_to_string('manual_pdf.html', ctx)
        buf = io.BytesIO()
        status = pisa.CreatePDF(src=html, dest=buf, encoding='utf-8')
        if status.err:
            return None
        buf.seek(0)
        return buf

    # -------- Helper: collect {heading_title: page_num} from PDF outlines
    def _collect_outline_pages(pdf_buf):
        pdf_buf.seek(0)
        reader = PdfReader(pdf_buf)
        pages_by_title = {}

        def walk(outlines):
            for item in outlines:
                if isinstance(item, list):
                    walk(item)
                else:
                    try:
                        title = item.title
                        page_0 = reader.get_destination_page_number(item)
                        if title not in pages_by_title:  # first occurrence wins
                            pages_by_title[title] = page_0 + 1
                    except Exception:
                        pass

        if reader.outline:
            walk(reader.outline)
        return pages_by_title

    # -------- Helper: inject page numbers into context tree --------
    def _inject_page_numbers(ctx, outline_pages):
        for group in ctx['pdf_groups']:
            group['page_num'] = outline_pages.get(group['name'], '')
            for chapter in group['chapters']:
                if chapter.get('module'):
                    m = chapter['module']
                    m['page_num'] = outline_pages.get(m['name'], '')
                for nested in chapter.get('nested', []):
                    for nm in nested['modules']:
                        # Template renders nested h3 as "Name (SubSection)"
                        composite_key = f"{nm['name']} ({nested['name']})"
                        nm['page_num'] = outline_pages.get(
                            composite_key,
                            outline_pages.get(nm['name'], '')
                        )
            for osc in group.get('orphan_sub_chapters', []):
                for om in osc['modules']:
                    composite_key = f"{om['name']} ({osc['name']})"
                    om['page_num'] = outline_pages.get(
                        composite_key,
                        outline_pages.get(om['name'], '')
                    )

    # -------- STEP 2: first xhtml2pdf pass ------------------------
    body_pass1 = _render_body(context)
    if body_pass1 is None:
        return HttpResponse(
            'PDF generation failed (first pass).',
            status=500, content_type='text/plain'
        )

    # -------- STEP 3: read outlines, inject page numbers ----------
    outline_pages = _collect_outline_pages(body_pass1)
    _inject_page_numbers(context, outline_pages)

    # -------- STEP 4: second xhtml2pdf pass -----------------------
    body_pass2 = _render_body(context)
    if body_pass2 is None:
        return HttpResponse(
            'PDF generation failed (second pass).',
            status=500, content_type='text/plain'
        )

    # -------- STEP 5: build footer overlay ------------------------
    body_pass2.seek(0)
    body_reader = PdfReader(body_pass2)
    num_pages = len(body_reader.pages)

    footer_text = (
        f"Alivente Online \u2014 User Manual   |   "
        f"Generated for {full_name} on {timezone.now().strftime('%d %b %Y')}"
    )

    overlay_buf = io.BytesIO()
    c = rl_canvas.Canvas(overlay_buf, pagesize=A4)
    page_w, page_h = A4
    margin_pt = 56.7          # 2cm in PDF points
    footer_line_y = 56.7
    footer_text_y = 42

    for page_num in range(1, num_pages + 1):
        # Skip footer on the cover page (page 1)
        if page_num == 1:
            c.showPage()
            continue

        c.setStrokeColorRGB(0.87, 0.88, 0.89)  # #dee2e6
        c.setLineWidth(0.5)
        c.line(margin_pt, footer_line_y, page_w - margin_pt, footer_line_y)

        c.setFont('Helvetica', 8.5)
        c.setFillColorRGB(0.42, 0.46, 0.49)   # #6c757d
        page_info = f"   |   Page {page_num} of {num_pages}"
        c.drawCentredString(page_w / 2, footer_text_y, footer_text + page_info)

        c.showPage()

    c.save()
    overlay_buf.seek(0)

    # -------- STEP 6: merge overlay onto body pages ---------------
    body_pass2.seek(0)
    body_reader = PdfReader(body_pass2)
    overlay_reader = PdfReader(overlay_buf)
    writer = PdfWriter()

    for i, page in enumerate(body_reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)

    # -------- Ship the PDF inline so preview iframe can render it
    today = timezone.now().strftime('%Y-%m-%d')
    filename = f"alivente_user_manual_{request.user.username}_{today}.pdf"

    response = HttpResponse(final_buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response['X-Manual-Filename'] = filename
    response['Access-Control-Expose-Headers'] = 'X-Manual-Filename'
    return response