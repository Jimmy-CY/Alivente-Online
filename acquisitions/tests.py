from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from .models import Criterion, Property, Scenario, ScenarioMatch
from .scoring import evaluate


class ScoringTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_acquisitions", verbosity=0)
        cls.apt = Scenario.objects.get(slug="apartment-to-renovate-nicosia")
        cls.plot = Scenario.objects.get(slug="building-plot-engomi-archangelos")

    def flat(self, **over):
        from .models import Area
        facts = dict(property_type="apartment", title="Test flat", area=Area.objects.get(name="Engomi"),
                     asking_price=Decimal("700000"), vat_status="none",
                     internal_m2=Decimal("250"), internal_m2_confirmed=True,
                     covered_balcony_m2=Decimal("50"), bedrooms=3, bathrooms=3, guest_wc=True,
                     master_ensuite=True, open_plan=True, parking_spaces=2, parking_covered=True,
                     whole_floor=True, lift=True, storeroom=True, year_built=2000,
                     condition="unrenovated")
        facts.update(over)
        return Property.objects.create(**facts)

    def test_perfect_flat_scores_by_the_rules(self):
        r = evaluate(self.apt, self.flat())
        # 20 + 20 + 10 preferred, area fit 15, price 15 * 0.5, balcony 10, year 10
        self.assertTrue(r.passes_musts)
        self.assertEqual(r.score, Decimal("92.5"))
        self.assertFalse(r.is_capped)

    def test_plus_vat_adds_19_percent(self):
        p = self.flat(asking_price=Decimal("700000"), vat_status="plus_vat")
        self.assertEqual(p.price_incl_vat, Decimal("833000"))
        self.assertIn("Budget ≤ €800k incl. VAT", evaluate(self.apt, p).failed_musts)

    def test_unknown_must_caps_score(self):
        r = evaluate(self.apt, self.flat(open_plan=None))
        self.assertTrue(r.passes_musts)
        self.assertTrue(r.is_capped)
        self.assertEqual(r.score, Decimal("60"))

    def test_unconfirmed_internal_area_is_unknown_for_must_but_scored(self):
        r = evaluate(self.apt, self.flat(internal_m2_confirmed=False))
        self.assertIn("Internal area 200–300 m²", r.unknown_musts)
        fit = next(b for b in r.breakdown if b.label == "Internal area fit")
        self.assertEqual(fit.points, Decimal("15"))

    def test_bathroom_group_counts_once(self):
        r = evaluate(self.apt, self.flat(guest_wc=None, master_ensuite=None, bathrooms=None,
                                         open_plan=None, lift=None))
        # 3 bathroom rules = 1 group, + open plan + lift = 3 unknown groups → still addable
        self.assertTrue(r.addable)
        r = evaluate(self.apt, self.flat(guest_wc=None, open_plan=None, lift=None, storeroom=None))
        self.assertTrue(r.addable)   # 4 groups - the limit is 4 (RA18)
        r = evaluate(self.apt, self.flat(guest_wc=None, open_plan=None, lift=None, storeroom=None,
                                         covered_balcony_m2=None))
        self.assertFalse(r.addable)  # 5 groups

    def test_clear_failure_rejects_unless_user_set(self):
        p = self.flat(open_plan=False)
        m = ScenarioMatch.objects.create(scenario=self.apt, property=p)
        from .scoring import apply_score
        apply_score(m)
        self.assertEqual(m.status, "rejected")
        m.set_status_by_user("shortlisted")
        apply_score(m)
        self.assertEqual(m.status, "shortlisted")
        self.assertFalse(m.passes_musts)

    def test_editing_a_criterion_rescores_existing_matches(self):
        p = self.flat(asking_price=Decimal("780000"))
        m = ScenarioMatch.objects.create(scenario=self.apt, property=p)
        from .scoring import apply_score
        apply_score(m)
        before = m.score
        c = Criterion.objects.get(scenario=self.apt, label="Price headroom")
        c.zero_above = Decimal("900000")
        c.save()
        m.refresh_from_db()
        self.assertGreater(m.score, before)

    def test_plot_buildable_maths(self):
        from .models import Area
        p = Property.objects.create(property_type="plot", title="Plot", area=Area.objects.get(name="Archangelos"),
                                    asking_price=Decimal("311500"), vat_status="none",
                                    plot_m2=Decimal("840"), building_density_pct=Decimal("90"),
                                    road_frontages=2, title_deeds=True)
        self.assertEqual(p.buildable_m2, Decimal("756"))
        self.assertEqual(p.price_per_buildable_m2, Decimal("412"))
        self.assertEqual(p.price_per_m2, Decimal("371"))
        self.assertTrue(evaluate(self.plot, p).passes_musts)
