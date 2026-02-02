from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_custom.urls')),        # Nouvelle app auth
    path('api/accounts/', include('apps.accounts.urls')), # Garder accounts pour preferences
    path('api/', include('apps.brokers.urls')),
    path('api/', include('apps.core.urls')),                    # APIs Heartbeat Module 2
    path('api/trading-manual/', include('apps.trading_manual.urls')),  # Module 3 Trading Manuel
    path('', include('apps.webhooks.urls')),  # Module 4 Webhooks
    # ... autres URLs ...
]