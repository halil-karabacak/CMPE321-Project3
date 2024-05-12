# In urls.py
from django.urls import path
from .views import login, authenticate, add_user, update_stadium_name, coach_dashboard, delete_match_session, add_match_session, create_squad

urlpatterns = [
    path('login/', login, name='login'),
    path('authenticate/', authenticate, name='authenticate'),
    path('add-user/', add_user, name='add_user'),
    path('update_stadium/', update_stadium_name, name='update_stadium'),
    path('coach_dashboard/', coach_dashboard, name='coach_dashboard'),
    path('delete_match_session/', delete_match_session, name='delete_match_session'),
    path('add_match_session/', add_match_session, name='add_match_session'),
    path('create_squad/', create_squad, name='create_squad'),
]
