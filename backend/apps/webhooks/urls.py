# -*- coding: utf-8 -*-
"""
MODULE 4 - WEBHOOKS URLS
Configuration des routes API REST pour webhooks
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookViewSet, WebhookStateViewSet

# Router DRF pour ViewSets
router = DefaultRouter()
router.register(r'webhooks', WebhookViewSet, basename='webhook')
router.register(r'webhook-states', WebhookStateViewSet, basename='webhook-state')

urlpatterns = [
    path('api/', include(router.urls)),
]
