# In urls.py
from django.urls import path
from .views import login, authenticate, add_user, update_stadium_name

urlpatterns = [
    path('login/', login, name='login'),
    path('authenticate/', authenticate, name='authenticate'),
    path('add-user/', add_user, name='add_user'),
    path('update_stadium/', update_stadium_name, name='update_stadium'),
]
