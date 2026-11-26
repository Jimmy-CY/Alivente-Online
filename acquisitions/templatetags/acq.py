"""Template filters for the Acquisitions screens - RA19, 23 Nov 2026."""
from django import template
from django.utils.html import format_html

register = template.Library()


def _s():
    # The services module - and through it the app's models - is imported
    # when a filter runs, never when this file loads. A tag library is
    # imported by every Engine that is handed it, including a bare one with
    # no Acquisitions app installed (test_banner_pages hands over every
    # templatetags module in the repo), and a models import there fails.
    from acquisitions import services
    return services

PILLS = {"new": ("alv-pill-info", "New"), "active": ("alv-pill-good", "Active"),
         "price_changed": ("alv-pill-attn", "Price changed"),
         "shortlisted": ("alv-pill-good", "Shortlisted"),
         "rejected": ("alv-pill-bad", "Rejected"), "removed": ("alv-pill-neutral", "Removed")}


@register.filter
def euros(v):
    return _s().euros(v)


@register.filter
def euros_k(v):
    return _s().euros(v, short=True)


@register.filter
def n(v):
    return _s().num(v)


@register.filter
def pill(status):
    cls, label = PILLS.get(status, ("alv-pill-neutral", str(status).replace("_", " ")))
    return format_html('<span class="alv-pill {}">{}</span>', cls, label)


@register.filter
def scorebar(score):
    """A score as a number over a short bar."""
    if score is None:
        return "—"
    pct = max(0, min(100, float(score)))
    tone = "is-good" if pct >= 60 else ("is-mid" if pct >= 35 else "is-low")
    return format_html('<span class="acq-score"><strong>{}</strong>'
                       '<span class="acq-scorebar"><span class="{}" style="width:{}%">'
                       '</span></span></span>', _s().num(round(score)), tone, round(pct))


@register.filter
def signed(v):
    """+2.3% / -0.8% / a dash."""
    if v is None:
        return "—"
    return ("+%s%%" if v > 0 else "%s%%") % _s().num(v).replace("-", "−")


@register.filter
def get(d, k):
    try:
        return d.get(k)
    except AttributeError:
        return None


@register.filter
def notetip(m):
    """RA29, 26 Nov 2026 - Demetri: "a little "i", where if I hover over, I
    can see my general comments or rejected comments for a property". A
    speech bubble beside the title, only when there is something of his to
    read: his comment in full, his decision and its reason, his viewings.
    Filled when there is a comment, outlined when there is only the rest.
    Hover or focus shows it; a tap pins it (a phone has no hover)."""
    from django.utils.html import escape
    from django.utils.safestring import mark_safe
    said = (m.your_comments or "").strip()
    parts = []
    if said:
        parts.append(format_html('<span class="acq-note-h">Your comment</span><span class="acq-note-p">{}</span>',
                                 mark_safe(escape(said).replace("\n", "<br>"))))
    if m.status_set_by_user:
        parts.append(format_html('<span class="acq-note-h">{} by you</span>{}', m.get_status_display(),
                                 format_html('<span class="acq-note-p">{}</span>', m.decision_note)
                                 if m.decision_note else ""))
    views = list(m.property.viewings.all())
    if views:
        parts.append(format_html('<span class="acq-note-h">Viewing{}</span>{}', "s" if len(views) > 1 else "",
                                 mark_safe("".join(format_html('<span class="acq-note-p">{}{}</span>',
                                                               "%d %s %d" % (v.viewed_on.day, v.viewed_on.strftime("%b"), v.viewed_on.year),
                                                               (" \u2013 " + v.notes) if v.notes else "")
                                                   for v in views))))
    if not parts:
        return ""
    return format_html(
        '<span class="acq-note"><button type="button" class="acq-note-btn" aria-label="Your notes on this listing" '
        'aria-expanded="false"><i class="{} fa-comment" aria-hidden="true"></i></button>'
        '<span class="acq-note-box" role="tooltip">{}</span></span>',
        "fas" if said else "far", mark_safe("".join(parts)))
