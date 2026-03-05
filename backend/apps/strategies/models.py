# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings


class Strategy(models.Model):
    """Strategie de trading Python creee par l'utilisateur."""

    TIMEFRAME_CHOICES = [
        ('1m', '1 minute'),
        ('3m', '3 minutes'),
        ('5m', '5 minutes'),
        ('15m', '15 minutes'),
        ('1h', '1 heure'),
        ('4h', '4 heures'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='strategies'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    code = models.TextField()
    timeframe = models.CharField(
        max_length=5,
        choices=TIMEFRAME_CHOICES,
        default='15m'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'strategies'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'timeframe']),
        ]
        verbose_name = 'Strategie'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return f"{self.name} ({self.timeframe}) - {self.user.username}"
