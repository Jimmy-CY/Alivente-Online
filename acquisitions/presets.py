"""
presets.py - RA19, 23 Nov 2026. The four "Start from a template" cards.

Each is a starting point for a new scenario: its type, its rules and their
points. Nothing is saved until you press Save scenario, and every rule can
be changed in the editor first. The first two are the two scenarios step 1
seeded; the last two are suggestions, mostly plain-words rules for Claude,
because yields and auction terms are things only the listing text can tell.
"""
from acquisitions.management.commands.seed_acquisitions import (APARTMENT_CRITERIA,
                                                                PLOT_CRITERIA)

BUY_TO_LET = [
    ("Budget", "price_incl_vat", "must", "lte", {"num_max": 300000}),
    ("2 or 3 bedrooms", "bedrooms", "must", "between", {"num_min": 2, "num_max": 3}),
    ("Gross yield at least 5%", "custom", "must", "judged",
     {"rule_text": "the gross yield from typical area rents is at least 5%"}),
    ("Tenant-ready condition", "condition", "preferred", "in",
     {"points": 30, "text_values": ["good", "renovated", "new"]}),
    ("Lift", "lift", "preferred", "is_true", {"points": 15}),
    ("Covered parking", "parking_covered", "preferred", "is_true", {"points": 15}),
    ("Price headroom", "price_incl_vat", "scoring", "lte",
     {"points": 40, "full_to": 220000, "zero_above": 300000}),
]

AUCTION = [
    ("Budget (reserve or asking)", "price_incl_vat", "must", "lte", {"num_max": 800000}),
    ("Sold by a bank or at auction", "custom", "must", "judged",
     {"rule_text": "the property is bank-owned or offered at a published auction"}),
    ("Title free of charges", "custom", "preferred", "judged",
     {"points": 30, "rule_text": "the notice says the title is free of mortgages and charges"}),
    ("Viewing offered", "custom", "preferred", "judged",
     {"points": 20, "rule_text": "a viewing date is offered before the deadline"}),
    ("Price headroom", "price_incl_vat", "scoring", "lte",
     {"points": 50, "full_to": 600000, "zero_above": 800000}),
]

TEMPLATES = {
    "home": {"title": "Home to renovate", "property_type": "apartment",
             "blurb": "Size, layout and condition rules, scored on price headroom",
             "icon": "fa-home", "criteria": APARTMENT_CRITERIA},
    "plot": {"title": "Development plot", "property_type": "plot",
             "blurb": "Zone, density and €/buildable m²",
             "icon": "fa-vector-square", "criteria": PLOT_CRITERIA},
    "let": {"title": "Buy-to-let", "property_type": "apartment",
            "blurb": "Gross yield from area rents, tenant-ready condition",
            "icon": "fa-key", "criteria": BUY_TO_LET},
    "auction": {"title": "Auction & bank-owned", "property_type": "any",
                "blurb": "Reserve price, auction date and deposit tracking",
                "icon": "fa-gavel", "criteria": AUCTION},
}


def criteria_dicts(key):
    """The template's rules as the editor's JSON rows (no ids: all new)."""
    out = []
    for label, field, kind, op, extra in TEMPLATES[key]["criteria"]:
        row = {"id": None, "label": label, "field": field, "kind": kind, "operator": op,
               "num_min": None, "num_max": None, "text_values": [], "points": 0,
               "full_from": None, "full_to": None, "zero_below": None, "zero_above": None,
               "score_bands": [], "group": "", "rule_text": ""}
        row.update(extra)
        out.append(row)
    return out
