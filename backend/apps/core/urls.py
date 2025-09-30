from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration des routes API avec DRF Router
router = DefaultRouter()
router.register(r'positions', views.PositionViewSet, basename='position')
router.register(r'heartbeat', views.HeartbeatViewSet, basename='heartbeat')

app_name = 'core'

urlpatterns = [
    # Routes DRF - pas de 'api/' ici car deja dans aristobot/urls.py
    path('', include(router.urls)),
    # Route publique pour historique Heartbeat (sans auth)
    path('heartbeat-history/', views.HeartbeatHistoryView.as_view(), name='heartbeat-history'),
]
