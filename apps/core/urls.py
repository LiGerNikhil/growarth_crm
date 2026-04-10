from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users, name='users'),
    path('settings/', views.settings, name='settings'),
    path('profile/', views.profile, name='profile'),
]
