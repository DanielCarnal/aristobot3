# -*- coding: utf-8 -*-
from django.db import models

class DebugMode(models.Model):
    """
    Singleton pour l'état du mode debug.
    Permet d'activer/désactiver le mode développement depuis l'interface.
    """
    is_active = models.BooleanField(
        default=False,
        help_text="Mode debug actif (permet auto-login avec 'dev')"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'debug_mode'
        verbose_name = 'Mode Debug'
        verbose_name_plural = 'Mode Debug'
    
    @classmethod
    def get_state(cls):
        """Récupère l'état actuel du mode debug"""
        obj, created = cls.objects.get_or_create(id=1)
        return obj.is_active
    
    @classmethod
    def set_state(cls, active):
        """Définit l'état du mode debug"""
        obj, created = cls.objects.get_or_create(id=1)
        obj.is_active = active
        obj.save()
        return obj.is_active
    
    @classmethod
    def toggle(cls):
        """Bascule l'état du mode debug"""
        obj, created = cls.objects.get_or_create(id=1)
        obj.is_active = not obj.is_active
        obj.save()
        return obj.is_active
    
    def __str__(self):
        return f"Debug Mode: {'ON' if self.is_active else 'OFF'}"
