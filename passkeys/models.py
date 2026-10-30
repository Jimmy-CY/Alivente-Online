# -*- coding: utf-8 -*-
"""passkeys/models.py - PK-1, 30 Oct 2026.

A passkey is a key pair made by the phone. Its PRIVATE half never leaves
the phone (it is unlocked by the fingerprint); the server keeps only the
public half, below, which can check a signature but cannot make one. A
copy of this table is therefore no use to anybody trying to log in.
"""
from django.conf import settings
from django.db import models


class Passkey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='passkeys')
    # base64url of the credential id the phone chose; how a sign-in finds
    # its row. 255, NOT 512 - 0002: Alivente runs on MySQL, which does not
    # promise to index a unique column longer than 255 (mysql.W003). A
    # phone's id is 16 to 64 bytes, 22 to 86 characters here.
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.BinaryField()
    sign_count = models.PositiveBigIntegerField(default=0)
    # A plain description of where it was made ("Android phone"), so the
    # list on My Profile says which one to remove.
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'passkeys'
        ordering = ['-created_at']

    def __str__(self):
        return '%s - %s' % (self.user, self.name)
