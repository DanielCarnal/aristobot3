from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_custom.urls')),        # Nouvelle app auth
    path('api/accounts/', include('apps.accounts.urls')), # Garder accounts pour preferences
    path('api/', include('apps.brokers.urls')),
    # ... autres URLs ...
]