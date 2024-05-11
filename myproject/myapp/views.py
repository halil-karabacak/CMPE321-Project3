from django.shortcuts import render
from django.db import connection


def login(request):
    return render(request, 'login.html')


def authenticate(request):
    from django.shortcuts import render
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
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM DatabaseManager WHERE username = %s AND password = %s", [username, password])
            user = cursor.fetchone()
            if user:
                return render(request, 'admin_dashboard.html', {'username': username})
            return render(request, 'login.html', {'error': 'Invalid username or password'})


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
        additional_info = request.POST.get('additional_info') 

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
            return render(request, 'admin_dashboard.html')
        else:
            messages.error(request, 'Invalid user type.')

    return render(request, 'add_user.html')


def update_stadium_name(request):
    from django.shortcuts import render, redirect
    from django.db import connection
    from django.contrib import messages
    if request.method == 'POST':
        stadium_id = request.POST.get('stadium_id')
        new_name = request.POST.get('new_name')
        
        with connection.cursor() as cursor:
            cursor.execute("UPDATE Stadium SET stadium_name = %s WHERE stadium_ID = %s", [new_name, stadium_id])
            messages.success(request, 'Stadium name updated successfully.')
            return redirect('admin_dashboard')
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT stadium_ID, stadium_name FROM Stadium")
            stadiums = cursor.fetchall()

    return render(request, 'update_stadium.html', {'stadiums': stadiums})