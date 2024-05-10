# In urls.py
from django.urls import path
from .views import login, authenticate

urlpatterns = [
    path('login/', login, name='login'),
    path('authenticate/', authenticate, name='authenticate'),
]
