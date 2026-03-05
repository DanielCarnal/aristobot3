# -*- coding: utf-8 -*-
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StrategyViewSet

router = DefaultRouter()
router.register(r'', StrategyViewSet, basename='strategy')

urlpatterns = [
    path('', include(router.urls)),
]
