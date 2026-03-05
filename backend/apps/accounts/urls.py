from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('current/', views.current_user, name='current-user'),
    path('preferences/', views.update_preferences, name='update-preferences'),
    path('update-preferences/', views.update_preferences, name='update-preferences-alias'),
    path('test-ia/', views.test_ia_connection, name='test-ia-connection'),
]