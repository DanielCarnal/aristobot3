# -*- coding: utf-8 -*-
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class DevModeBackend(BaseBackend):
    """
    Backend d'authentification pour le mode développement.
    Connecte automatiquement l'utilisateur 'dev' si DEBUG=True
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if settings.DEBUG and not username:
            # En mode DEBUG, retourner automatiquement l'user dev
            try:
                return User.objects.get(username='dev')
            except User.DoesNotExist:
                return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None