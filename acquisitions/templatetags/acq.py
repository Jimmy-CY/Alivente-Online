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
