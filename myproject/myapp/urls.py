# In urls.py
from django.urls import path
from .views import login, authenticate, add_user, admin_login, admin_dashboard

urlpatterns = [
    path('login/', login, name='login'),
    path('authenticate/', authenticate, name='authenticate'),
    path('add-user/', add_user, name='add_user'),
    path('admin-login/', admin_login, name='admin_login'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),

]
