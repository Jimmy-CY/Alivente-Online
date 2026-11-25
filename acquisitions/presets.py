"""
presets.py - RA19, 23 Nov 2026. The "Start from a template" cards (three
since RA22: Home to renovate, Development plot, Home to rent).

Each is a starting point for a new scenario: its type, its rules and their
points. Nothing is saved until you press Save scenario, and every rule can
be changed in the editor first. The first two are the two scenarios step 1
seeded; Home to rent is a starting point to change before saving.
"""
from acquisitions.management.commands.seed_acquisitions import (APARTMENT_CRITERIA,
                                                                PLOT_CRITERIA)

# RA22, 24 Nov 2026 - Buy-to-let and Auction & bank-owned are gone; Home to
# rent takes their place (Demetri: "remove the Start from a template
# Buy-to-Let and Auction & bank-owned. Add a new one - Home to rent").
HOME_TO_RENT = [
    ("Location", "area", "must", "in", {"text_values": ["Engomi", "Makedonitissa", "Strovolos"]}),
    ("Rent ≤ €2,000 a month", "monthly_rent", "must", "lte", {"num_max": 2000}),
    ("Bedrooms at least 3", "bedrooms", "must", "gte", {"num_min": 3}),
    ("At least 2 bathrooms", "bathrooms", "must", "gte", {"num_min": 2, "group": "bathrooms"}),
    ("Rent headroom", "monthly_rent", "scoring", "lte",
     {"points": 40, "full_to": 1500, "zero_above": 2000}),
    ("Covered parking", "parking_covered", "preferred", "is_true", {"points": 20}),
    ("Lift", "lift", "preferred", "is_true", {"points": 15}),
    ("Furnished", "furnished", "preferred", "is_true", {"points": 15}),
    ("Storeroom", "storeroom", "preferred", "is_true", {"points": 10}),
]

TEMPLATES = {
    "home": {"title": "Home to renovate", "property_type": "apartment",
             "blurb": "Size, layout and condition rules, scored on price headroom",
             "icon": "fa-home", "criteria": APARTMENT_CRITERIA},
    "plot": {"title": "Development plot", "property_type": "plot",
             "blurb": "Zone, density and €/buildable m²",
             "icon": "fa-vector-square", "criteria": PLOT_CRITERIA},
    "rent": {"title": "Home to rent", "property_type": "apartment", "deal": "rent",
             "blurb": "Rent a month, rooms, furnished and parking",
             "icon": "fa-key", "criteria": HOME_TO_RENT},
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
