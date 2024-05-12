from django.shortcuts import render
from django.db import connection


coach_username_to_session_id = {}


def login(request):
    return render(request, 'login.html')


def authenticate(request):
    from django.shortcuts import render
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        cursor = connection.cursor()
        request.session['username'] = username
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
            else:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM Coach WHERE username = %s AND password = %s", [username, password])
                user = cursor.fetchone()
                if user:
                    cursor.execute("SELECT username, name, surname FROM Jury")
                    juries = cursor.fetchall()
                    return render(request, 'coach_dashboard.html', {'juries': juries, 'username': username})
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
            return render(request, 'admin_dashboard.html',  {'username': request.user.username})
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT stadium_ID, stadium_name FROM Stadium")
            stadiums = cursor.fetchall()
        return render(request, 'update_stadium.html', {'stadiums': stadiums})


def coach_dashboard(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT username, name, surname FROM Jury")
        juries = cursor.fetchall()
        return render(request, 'coach_dashboard.html', {'juries': juries, 'username': request.user.username})


def delete_match_session(request):
    from django.shortcuts import render, redirect
    from django.db import connection
    from django.contrib import messages
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM SessionSquads WHERE session_ID = %s", [session_id])
            cursor.execute("DELETE FROM MatchSession WHERE session_ID = %s", [session_id])
            messages.success(request, f'Match session {session_id} and related data deleted successfully.')
        
        return redirect('coach_dashboard')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('coach_dashboard')


def fetch_current_team_id(coach_username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT team_ID FROM Team WHERE coach_username = %s", [coach_username])
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None


def add_match_session(request):
    from django.shortcuts import render, redirect
    from django.db import connection
    from django.contrib import messages
    from django.contrib.auth.decorators import login_required
    if request.method == 'POST':
        stadium_id = request.POST.get('stadium_id')
        date = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        jury_username = request.POST.get('jury_username')
        username = request.session.get('username')

        current_team_id = fetch_current_team_id(username)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO MatchSession (team_ID, stadium_ID, date, time_slot, assigned_jury_username)
                VALUES (%s, %s, %s, %s, %s)
            """, [current_team_id, stadium_id, date, time_slot, jury_username])
            cursor.execute("SELECT LAST_INSERT_ID()")
            session_id = cursor.fetchone()[0]
            coach_username_to_session_id[request.session.get('username')] = session_id

            messages.success(request, 'New match session added successfully.')
        return coach_dashboard(request)
    else:
        return coach_dashboard(request)
    


def create_squad(request):
    from django.shortcuts import render, redirect
    from django.db import connection
    from django.contrib import messages
    
    session_id = coach_username_to_session_id[request.session.get('username')]

    if request.method == 'POST':
        player_positions = zip(request.POST.getlist('player_usernames'), request.POST.getlist('position_ids'))
        current_team_id = fetch_current_team_id(request.session.get('username'))

        with connection.cursor() as cursor:
            
            cursor.execute("""
                SELECT username FROM PlayerTeams WHERE team = %s
            """, [current_team_id])
            valid_players = {row[0] for row in cursor.fetchall()}

            for player, pos in player_positions:
                if player in valid_players:
                    cursor.execute("""
                        INSERT INTO SessionSquads (session_ID, played_player_username, position_ID)
                        VALUES (%s, %s, %s)
                    """, [session_id, player, pos])
            messages.success(request, "Squad created successfully.")
            return redirect('coach_dashboard')

    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username FROM PlayerTeams WHERE team = %s
            """, [fetch_current_team_id(request.session.get('username'))])
            players = cursor.fetchall()
        return render(request, 'create_squad.html', {'players': players, 'session_id': session_id})

