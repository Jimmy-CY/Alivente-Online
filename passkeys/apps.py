from django.apps import AppConfig


class PasskeysConfig(AppConfig):
    """PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys/WebAuthn).

    Its own small app with NO templates: the button lives on the house
    login page and the list on My Profile, so the template tree does not
    grow and no census moves. The password stays as the fallback.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'passkeys'
    verbose_name = 'Passkeys'
