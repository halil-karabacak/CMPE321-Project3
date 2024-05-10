from django.shortcuts import render
from django.db import connection


def login(request):
    return render(request, 'login.html')

def authenticate(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM player WHERE username = %s AND password = %s", [username, password])
        user = cursor.fetchone()
        if user:
            # Authentication successful, redirect to dashboard or home page
            return render(request, 'home.html', {'username': username})
        else:
            # Authentication failed, render login page with error message
            return render(request, 'login.html', {'error': 'Invalid username or password'})
