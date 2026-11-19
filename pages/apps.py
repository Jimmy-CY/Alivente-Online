from django.apps import AppConfig

class PagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"
    
    def ready(self):
        """Import signals when app is ready"""
        import pages.signals
        # SY-1, 26 Oct 2026 - every module permission exists after every
        # migrate (pages/permissions.py, ensure_permissions). sender=self:
        # once per migrate, after this app's migrations; the dispatch_uid
        # keeps a second ready() from connecting it twice.
        from django.db.models.signals import post_migrate
        post_migrate.connect(_ensure_permissions, sender=self,
                             dispatch_uid='pages.ensure_permissions')
        # RA04, 19 Nov 2026 - an email when a key stops working
        # (pages/key_health.py): every Anthropic call reports how it went,
        # and on Railway a watcher checks the keys every 15 minutes.
        try:
            from pages import key_health
            key_health.wrap_anthropic()
            key_health.start_watcher()
        except Exception:  # never stops the app starting
            pass


def _ensure_permissions(sender, using='default', verbosity=1, **kwargs):
    from pages.permissions import ensure_permissions
    made = ensure_permissions(using)
    if made and verbosity:
        print('  Created %d permission(s): %s' % (len(made), ', '.join(made)))