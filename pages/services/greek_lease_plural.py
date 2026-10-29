# -*- coding: utf-8 -*-
"""greek_lease_plural.py - GL-3, 29 Oct 2026.

THE GREEK LEASE FOR TWO TENANTS. The Greece template is written for one
tenant: "Aφ'ετέρου η/ο ... καλούμενη εφεξής η «μισθώτρια»", and nineteen
places after that speak of "η μισθώτρια" in the singular. His decisions of
29 October: the details are captured PER tenant, and when there is a second
tenant the lease names both - "καλούμενοι εφεξής από κοινού «οι μισθωτές»"
- with every reference after it in the plural.

THE TEMPLATE IS NOT EDITED. A one-tenant lease is byte-for-byte what it
was. For two tenants the rendered document is rewritten here, phrase by
phrase, each phrase whole so the verb and the pronoun change with the noun
("Η μισθώτρια ευθύνεται ... υπαιτιότητά της" -> "Οι μισθωτές ευθύνονται
... υπαιτιότητά τους").

FAIL LOUD. Every phrase must be found exactly as many times as listed. A
template that changed shape raises ValueError rather than send a lease that
is half singular - and afterwards no singular "μισθώτρια" may remain.
"""
import re

# (singular, plural, times). Order matters only where one phrase contains
# another; the longer comes first.
PHRASES = [
    # 1. ΜΙΣΘΙΟ
    ('εκμισθώνει η εκμισθώτρια στην μισθώτρια, η οποία δέχεται',
     'εκμισθώνει η εκμισθώτρια στους μισθωτές, οι οποίοι δέχονται', 1),
    # 2. ΔΙΑΡΚΕΙΑ
    ('η μισθώτρια είναι υποχρεωμένη',
     'οι μισθωτές είναι υποχρεωμένοι', 1),
    # 4. ΧΡΗΣΗ
    ('για οικία της μισθώτριας, καθώς και της οικογενείας αυτής',
     'για οικία των μισθωτών, καθώς και της οικογενείας τους', 1),
    ('απαγορεύεται απόλυτα στη μισθώτρια',
     'απαγορεύεται απόλυτα στους μισθωτές', 1),
    # 5. ΠΑΡΑΛΑΒΗ - ΕΠΙΣΚΕΥΕΣ
    ('Η μισθώτρια δηλώνει', 'Οι μισθωτές δηλώνουν', 1),
    ('Η μισθώτρια έχει την υποχρέωση να ενημερώσει',
     'Οι μισθωτές έχουν την υποχρέωση να ενημερώσουν', 1),
    ('Η μισθώτρια ευθύνεται να αποκαταστήσει όποια βλάβη οφείλεται σε '
     'αποκλειστική υπαιτιότητά της',
     'Οι μισθωτές ευθύνονται να αποκαταστήσουν όποια βλάβη οφείλεται σε '
     'αποκλειστική υπαιτιότητά τους', 1),
    # 6. ΠΡΟΣΘΗΚΕΣ
    ('Απαγορεύεται στη μισθώτρια να επιφέρει',
     'Απαγορεύεται στους μισθωτές να επιφέρουν', 1),
    # 7. ΚΑΛΗ ΧΡΗΣΗ
    ('Η μισθώτρια υποχρεούται να κάνει καλή και επιμελή χρήση του μισθίου '
     'και να ενημερώνει',
     'Οι μισθωτές υποχρεούνται να κάνουν καλή και επιμελή χρήση του '
     'μισθίου και να ενημερώνουν', 1),
    ('Επίσης υποχρεούται η μισθώτρια να διατηρεί',
     'Επίσης υποχρεούνται οι μισθωτές να διατηρούν', 1),
    ('να μην ενοχλεί', 'να μην ενοχλούν', 1),
    ('να μην καταλαμβάνει', 'να μην καταλαμβάνουν', 1),
    ('να μην αποθηκεύει', 'να μην αποθηκεύουν', 1),
    ('να μην αποθέτει', 'να μην αποθέτουν', 1),
    ('να μην διαταράσσει', 'να μην διαταράσσουν', 1),
    # 8. ΛΟΓΑΡΙΑΣΜΟΙ - ΤΕΛΗ
    ('θα βαρύνουν αποκλειστικώς την μισθώτρια',
     'θα βαρύνουν αποκλειστικώς τους μισθωτές', 1),
    ('Επίσης η μισθώτρια υποχρεούται να καταβάλλει',
     'Επίσης οι μισθωτές υποχρεούνται να καταβάλλουν', 1),
    ('Η μισθώτρια ήδη έχει συνάψει', 'Οι μισθωτές ήδη έχουν συνάψει', 1),
    ('στ’ όνομά της για το συγκεκριμένο ακίνητο',
     'στ’ όνομά τους για το συγκεκριμένο ακίνητο', 1),
    # 9. ΑΠΟΔΟΣΗ
    ('Η μισθώτρια υποχρεούται, χωρίς καμία όχληση',
     'Οι μισθωτές υποχρεούνται, χωρίς καμία όχληση', 1),
    ('να παραδώσει στην εκμισθώτρια τη χρήση του μισθίου στην κατάσταση '
     'που το παρέλαβε',
     'να παραδώσουν στην εκμισθώτρια τη χρήση του μισθίου στην κατάσταση '
     'που το παρέλαβαν', 1),
    ('διαφορετικά υποχρεούται σε καταβολή',
     'διαφορετικά υποχρεούνται σε καταβολή', 1),
    # 12. ΕΠΙΣΚΕΨΗ
    ('κατόπιν συνεννόησης με την μισθώτρια',
     'κατόπιν συνεννόησης με τους μισθωτές', 1),
    ('εάν η μισθώτρια τηρεί', 'εάν οι μισθωτές τηρούν', 1),
    # 16. ΟΡΟΙ
    ('την έξωση της μισθώτριας', 'την έξωση των μισθωτών', 1),
    # The signature heading (removed again for e-signing).
    ('Η ΜΙΣΘΩΤΡΙΑ', 'ΟΙ ΜΙΣΘΩΤΕΣ', 1),
]

# The tenant paragraph's ending, as the template renders it.
DEFINED = 'καλούμενη εφεξής η « μισθώτρια»,'

# A singular "μισθώτρια" in any case, not part of "εκμισθώτρια".
LEFT = re.compile(r'(?<![εΕ]κ)(?<!ΕΚ)(μισθώτρι|ΜΙΣΘΩΤΡΙ)')


def _paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def _replace_in(p, old, new):
    """Replace every `old` in paragraph p, across run boundaries, keeping
    the formatting of the run each match starts in. Returns the count."""
    n = 0
    start = 0
    while True:
        runs = p.runs
        text = ''.join(r.text for r in runs)
        # From after the last replacement: a `new` that contains `old`
        # (the signature line) must not be matched again.
        i = text.find(old, start)
        if i < 0:
            return n
        start = i + len(new)
        j = i + len(old)
        pos = 0
        first = True
        for r in runs:
            a, b = pos, pos + len(r.text)
            pos = b
            if b <= i or a >= j:
                continue
            s, e = max(i, a) - a, min(j, b) - a
            if first:
                r.text = r.text[:s] + new + r.text[e:]
                first = False
            else:
                r.text = r.text[:s] + r.text[e:]
        n += 1


def count(doc, phrase):
    return sum(''.join(r.text for r in p.runs).count(phrase)
               for p in _paragraphs(doc))


def pluralise(docx_path, second, first_name=''):
    """Rewrite a rendered one-tenant Greek lease for two tenants, in place.

    `second` holds name, father_name, address, afm, doy for the second
    tenant. Raises ValueError when the document is not the shape this was
    written against."""
    from docx import Document

    doc = Document(docx_path)
    if count(doc, DEFINED) != 1:
        raise ValueError('The Greek lease template has changed: the tenant '
                         'paragraph could not be found, so the second '
                         'tenant cannot be added to it.')
    for old, new, times in PHRASES:
        got = count(doc, old)
        if got != times:
            raise ValueError('The Greek lease template has changed: "%s" '
                             'was found %d time(s), expected %d, so the '
                             'lease cannot be written for two tenants.'
                             % (old[:60], got, times))
    added = ('και η/ο {name} του {father_name}, κάτοικος {address}, με '
             'Α.Φ.Μ.: {afm}, ΔΟΥ: {doy}, καλούμενοι εφεξής από κοινού «οι '
             'μισθωτές»,').format(**dict(
                 (k, (second.get(k) or '').strip()) for k in
                 ('name', 'father_name', 'address', 'afm', 'doy')))
    for p in _paragraphs(doc):
        _replace_in(p, DEFINED, added)
        for old, new, _t in PHRASES:
            _replace_in(p, old, new)
    # The signature line names the first tenant after tabs; the second
    # joins him there (removed again for e-signing).
    first_name = (first_name or '').strip()
    if first_name:
        for p in _paragraphs(doc):
            t = ''.join(r.text for r in p.runs)
            if '\t' in t and t.rstrip().endswith(first_name):
                _replace_in(p, first_name, '%s / %s' % (
                    first_name, (second.get('name') or '').strip()))
                break
    for p in _paragraphs(doc):
        if LEFT.search(''.join(r.text for r in p.runs)):
            raise ValueError('The Greek lease still says "μισθώτρια" in the '
                             'singular after it was written for two '
                             'tenants: "%s"' % p.text[:80])
    doc.save(docx_path)
    return True
