"""
Management command: seed_ingredient_families

Creates the WCIM ingredient families and assigns their members. Idempotent —
safe to re-run after edits to the FAMILIES dict below. Existing IngredientFamily
rows are updated in place, ingredient assignments are flipped to match the
seed as the source of truth.

Usage:
    python manage.py seed_ingredient_families
"""
from django.core.management.base import BaseCommand

from pages.models import Ingredient, IngredientFamily


# Each family: name → {description, ingredient_ids}.
# IDs come from Live. On local dev (small dataset) most IDs won't resolve
# and the command will print warnings — that's expected, not an error.
#
# WCIM family equivalence rules:
#   - Substitutability must be SAFE in MOST recipes that call for any member.
#   - Cross-context warnings live in the description so the user reading
#     admin can understand why we equated them.
#   - When in doubt: err narrow. Better to under-equate than create false matches.

FAMILIES = {

    # =========================================================================
    # SEASONINGS, HERBS, SPICES
    # =========================================================================

    "Salt forms": {
        "description": (
            "Different crystal sizes of the same sodium chloride. Substitute "
            "freely by weight for most cooking. Fine pastry/baking applications "
            "may prefer table salt specifically."
        ),
        "ingredient_ids": [
            22,   # Salt
            220,  # Salt, Coarse
            74,   # Salt, Flakes
        ],
    },

    "Black pepper forms": {
        "description": (
            "Same spice, different grind. Peppercorns require a grinder; "
            "ground black pepper is ready to use."
        ),
        "ingredient_ids": [
            26,   # Pepper, Ground Black
            280,  # Peppercorns
        ],
    },

    "Chilli heat powders": {
        "description": (
            "All deliver chilli heat. Cayenne is fine powder, chile powder "
            "often has cumin/garlic blended in, chilli flakes are coarse. "
            "Quantity may need scaling — chilli flakes are typically milder "
            "per teaspoon than pure cayenne."
        ),
        "ingredient_ids": [
            117,  # Pepper, Cayenne
            93,   # Chile Powder
            157,  # Chilli Flakes, Crushed
        ],
    },

    "Paprika forms": {
        "description": (
            "Both sweet paprika at base. Smoked is the flavour anchor in some "
            "recipes (paella, patatas bravas) where sweet won't deliver. "
            "Safe substitute for general seasoning."
        ),
        "ingredient_ids": [
            29,   # Paprika
            65,   # Paprika, Smoked
        ],
    },

    "Thyme forms": {
        "description": "Fresh ↔ dried thyme, standard 3:1 ratio (1 tsp dried ≈ 1 tbsp fresh).",
        "ingredient_ids": [
            260,  # Thyme, Fresh
            135,  # Thyme, Dried
        ],
    },

    "Parsley forms": {
        "description": "Fresh ↔ dried parsley, standard 3:1 ratio.",
        "ingredient_ids": [
            196,  # Parsley
            266,  # Parsley, Dried
        ],
    },

    # =========================================================================
    # SUGARS (non-baking — baking substitution is dangerous)
    # =========================================================================

    "White sugar forms": {
        "description": (
            "Both white sugar, caster is finer-ground. Interchangeable for "
            "general cooking. Baking-sensitive recipes may want caster "
            "specifically for texture."
        ),
        "ingredient_ids": [
            9,    # Sugar
            2,    # Caster Sugar
        ],
    },

    "Brown sugar forms": {
        "description": (
            "Both brown sugars with molasses, differ in concentration. "
            "Muscovado is darker and more intense."
        ),
        "ingredient_ids": [
            92,   # Sugar, Brown
            179,  # Sugar, Brown (muscovado)
        ],
    },

    # =========================================================================
    # DAIRY
    # =========================================================================

    "Milk forms": {
        "description": "Same product, full-cream is a specific fat level.",
        "ingredient_ids": [
            8,    # Milk
            254,  # Milk, Full Cream
        ],
    },

    "Cooking creams (savoury)": {
        "description": (
            "SAVOURY USE ONLY. Fresh cream, double cream, and coconut cream "
            "interchangeable in sauces, soups, curries. Coconut leaves a "
            "distinct flavour wanted in Thai/Indian, unwanted in French/Italian. "
            "NOT for desserts or baking — equivalence breaks down with sugar/fat "
            "chemistry."
        ),
        "ingredient_ids": [
            11,   # Cream, Fresh
            241,  # Cream, Double
            67,   # Coconut Cream
        ],
    },

    "Cheddar forms": {
        "description": "Same cheese, different aging. Mature is sharper but functionally identical in recipes.",
        "ingredient_ids": [
            43,   # Cheddar Cheese
            162,  # Cheddar Cheese, Mature
        ],
    },

    "Mozzarella forms": {
        "description": "Same cheese, different shape. Balls are usually fresh mozzarella in brine.",
        "ingredient_ids": [
            110,  # Mozzarella Cheese
            355,  # Mozzarella Balls
        ],
    },

    # =========================================================================
    # WINES & VINEGARS
    # =========================================================================

    "Wine vinegars": {
        "description": (
            "Red and white wine vinegar — quite interchangeable for deglazing, "
            "dressings, and sauces. Red can darken light-coloured dishes slightly."
        ),
        "ingredient_ids": [
            139,  # Vinegar, Red Wine
            90,   # Vinegar, White Wine
        ],
    },

    "White wines": {
        "description": (
            "Both white wines, dry vs semi-sweet. Substitute freely in savoury "
            "cooking; watch sweetness in reductions and pan sauces."
        ),
        "ingredient_ids": [
            189,  # Wine, White
            246,  # Wine, White Semi-sweet
        ],
    },

    # =========================================================================
    # VEGETABLES
    # =========================================================================

    "Onion forms": {
        "description": (
            "White/yellow ↔ red onions. Mostly interchangeable in cooked dishes; "
            "red is sharper raw and adds colour."
        ),
        "ingredient_ids": [
            40,   # Onion/s
            62,   # Onions, Red
        ],
    },

    "Bell peppers": {
        "description": (
            "Red, yellow, green bell peppers. Fully interchangeable in cooking. "
            "Green is slightly more bitter; red/yellow are sweeter."
        ),
        "ingredient_ids": [
            60,   # Bell Peppers, Red
            61,   # Bell Peppers, Yellow
            365,  # Bell Peppers, Green
        ],
    },

    "Spinach forms": {
        "description": (
            "All spinach. Baby is more tender; frozen is convenient but releases "
            "more water on thawing."
        ),
        "ingredient_ids": [
            23,   # Spinach
            111,  # Spinach, Baby
            257,  # Spinach, Frozen
        ],
    },

    "Sweetcorn (canned/frozen)": {
        "description": "Both pre-cooked sweetcorn kernels. Substitute freely.",
        "ingredient_ids": [
            370,  # Sweetcorn, Canned
            322,  # Sweetcorn, Frozen
        ],
    },

    "Tomato bases (chopped/passata)": {
        "description": (
            "Tinned chopped tomatoes and passata. Reasonably interchangeable in "
            "sauces, stews, ragùs. Chopped if recipe wants visible chunks; "
            "blend passata if smoothness needed."
        ),
        "ingredient_ids": [
            100,  # Tomatoes (chopped), Tinned
            163,  # Passata, Tomato
        ],
    },

    # =========================================================================
    # FISH & SEAFOOD
    # =========================================================================

    "White fish forms": {
        "description": "Same fish, different prep.",
        "ingredient_ids": [
            217,  # White Fish, Skin-on
            219,  # White Fish, Skin-off
        ],
    },

    "Mussels": {
        "description": "Same shellfish, different prep stage.",
        "ingredient_ids": [
            275,  # Mussels, With Shells
            276,  # Mussels, Without Shells
        ],
    },

    "Prawn forms": {
        "description": "Prawns frozen vs queen-size. Substitute, adjusting count for size differences.",
        "ingredient_ids": [
            283,  # Prawns, Frozen
            310,  # Prawns, Queen
        ],
    },

    # =========================================================================
    # SAUCES
    # =========================================================================

    "Nando's peri-peri": {
        "description": "Same product line, two heat levels. Adjust quantity for desired heat.",
        "ingredient_ids": [
            297,  # Nando's Peri-peri Sauce, Extra Hot
            159,  # Nando's Peri-peri Sauce, Hot
        ],
    },

    # =========================================================================
    # MEATS (Phase 3 original 5)
    # =========================================================================

    "Chicken cuts": {
        "description": (
            "Boneless and bone-in chicken pieces (breast, thigh) that work in "
            "most chicken recipes. Wings excluded (typically called for shape-"
            "specifically), whole chicken excluded (roasting cut)."
        ),
        "ingredient_ids": [
            184,  # Chicken Breasts, Skinless
            153,  # Chicken Breasts, Skin-on
            134,  # Chicken Thighs (boneless, Skinless)
            136,  # Chicken Thighs (bone-in)
        ],
    },

    "Pork chops": {
        "description": "Pork chops of different cuts. Interchangeable for grilling and pan-frying.",
        "ingredient_ids": [
            367,  # Pork Bacon Chops
            28,   # Pork Neck Chops
        ],
    },

    "Pork shoulder": {
        "description": (
            "Pork shoulder variants including the souvla cut. Rind on/off and "
            "bone in/out are cosmetic for most slow-cook recipes."
        ),
        "ingredient_ids": [
            317,  # Pork Shoulder (rind-off, bone-in)
            319,  # Pork Shoulder (rind-off, Deboned)
            318,  # Pork Shoulder (rind-on, Bone-in)
            320,  # Pork Shoulder (rind-on, Deboned)
            339,  # Pork Shoulder, Souvla
        ],
    },

    "Beef steaks": {
        "description": (
            "Tender beef cuts for fast cooking (steaks, peppercorn sauce, "
            "stir-fries). NOT brisket or oxtail — those are slow-cook only."
        ),
        "ingredient_ids": [
            120,  # Fillet, Beef
            187,  # Steak (beef), Sirloin
        ],
    },

    "Lamb roasting cuts": {
        "description": (
            "Large lamb cuts for roasting and slow cooking. NOT lamb chops or "
            "souvlaki — those are different in use."
        ),
        "ingredient_ids": [
            249,  # Lamb, Front Quarter
            248,  # Lamb, Leg
            251,  # Lamb, Shoulder
            338,  # Lamb Shoulder, Souvla
        ],
    },
}


class Command(BaseCommand):
    help = "Seed WCIM ingredient families with the curated groups. Idempotent."

    def handle(self, *args, **options):
        total_assigned = 0
        total_missing = 0
        total_unchanged = 0

        for family_name, family_data in FAMILIES.items():
            family, created = IngredientFamily.objects.get_or_create(
                name=family_name,
                defaults={"description": family_data["description"]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"+ Created family: {family_name}"))
            else:
                self.stdout.write(f"  Family exists: {family_name}")
                if family.description != family_data["description"]:
                    family.description = family_data["description"]
                    family.save()
                    self.stdout.write("    (description updated)")

            assigned_count = 0
            unchanged_count = 0
            missing_ids = []
            for ing_id in family_data["ingredient_ids"]:
                try:
                    ing = Ingredient.objects.get(ingredient_id=ing_id)
                    if ing.family_id != family.family_id:
                        ing.family = family
                        ing.save(update_fields=["family"])
                        assigned_count += 1
                    else:
                        unchanged_count += 1
                except Ingredient.DoesNotExist:
                    missing_ids.append(ing_id)

            total_assigned += assigned_count
            total_unchanged += unchanged_count
            total_missing += len(missing_ids)

            line = f"    Assigned: {assigned_count}"
            if unchanged_count:
                line += f", unchanged: {unchanged_count}"
            self.stdout.write(line)
            if missing_ids:
                self.stdout.write(self.style.WARNING(f"    Missing (not in DB): {missing_ids}"))

        total_families = IngredientFamily.objects.count()
        total_with_family = Ingredient.objects.filter(family__isnull=False).count()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done: {total_families} families total, "
            f"{total_with_family} ingredients have a family."
        ))
        self.stdout.write(
            f"This run: {total_assigned} newly assigned, "
            f"{total_unchanged} unchanged."
        )
        if total_missing:
            self.stdout.write(self.style.WARNING(
                f"({total_missing} IDs missing locally — expected on small dev dataset.)"
            ))