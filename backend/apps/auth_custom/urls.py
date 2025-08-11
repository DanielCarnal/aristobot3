# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # Endpoints standards (garde la logique existante)
    path('login/', views.login_view, name='auth-login'),
    path('logout/', views.logout_view, name='auth-logout'),
    path('register/', views.register_view, name='auth-register'),
    
    # Info user connecté + mode debug
    path('status/', views.status_view, name='auth-status'),
    
    # Configuration du mode debug
    path('debug-config/', views.debug_config_view, name='debug-config'),
    path('toggle-debug/', views.toggle_debug_view, name='toggle-debug'),
    path('debug-login/', views.debug_login_view, name='debug-login'),
    path('debug-auth/', views.debug_auth_view, name='debug-auth'),
    path('csrf-token/', views.csrf_token_view, name='csrf-token'),
]