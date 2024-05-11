# In urls.py
from django.urls import path
from .views import login, authenticate, add_user

urlpatterns = [
    path('login/', login, name='login'),
    path('authenticate/', authenticate, name='authenticate'),
    path('add-user/', add_user, name='add_user'),
]
