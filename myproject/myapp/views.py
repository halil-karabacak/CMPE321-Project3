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


def admin_login(request):
    from django.shortcuts import render, redirect
    from django.contrib.auth import authenticate, login
    from django.contrib import messages
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to an admin-specific dashboard
        else:
            messages.error(request, 'Invalid credentials or not an admin.')

    return render(request, 'admin_login.html')


def add_user(request):
    from django.shortcuts import render, redirect
    from django.db import connection
    from django.contrib import messages
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        additional_info = request.POST.get('additional_info')  # This could be date of birth for players, nationality for jury, etc.

        query = ""
        if user_type == 'player':
            query = """
            INSERT INTO Player (username, password, name, surname, date_of_birth)
            VALUES (%s, %s, %s, %s, %s)
            """
        elif user_type == 'jury':
            query = """
            INSERT INTO Jury (username, password, name, surname, nationality)
            VALUES (%s, %s, %s, %s, %s)
            """
        elif user_type == 'coach':
            query = """
            INSERT INTO Coach (username, password, name, surname, nationality)
            VALUES (%s, %s, %s, %s, %s)
            """
        
        if query:
            with connection.cursor() as cursor:
                cursor.execute(query, [username, password, name, surname, additional_info])
                messages.success(request, f'New {user_type} added successfully.')
            return redirect('add_user_form')
        else:
            messages.error(request, 'Invalid user type.')

    return render(request, 'add_user.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def admin_only(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(admin_only)
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')