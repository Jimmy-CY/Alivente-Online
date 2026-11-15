from django.apps import AppConfig


class TravelConfig(AppConfig):
    """TR-1, 15 Nov 2026 - the Travel module.

    ITS OWN APP, LIKE WELLNESS. Demetri, 15 Nov: a section of the main app
    on the desktop now, and later its own installable phone app (offline
    passes, "Share -> Alivente Travel"), as Wellness is. Its templates live
    in travel/templates, outside alv_tree.TEMPLATE_ROOTS; they extend the
    main app's base.html and use its classes, and test_travel_one.py is
    what holds them to account.

    WHO SEES WHAT. A trip belongs to the person who made it. Shared, like a
    meal plan, everyone it is shared with sees and changes it - all of it,
    costs included (Demetri, 15 Nov: "Everyone can see everyone's costs");
    only the owner changes who that is, or deletes it. Unshared, it is the
    owner's alone - superusers included: every lookup goes through
    trips_for(user).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'travel'
    verbose_name = 'Travel'
