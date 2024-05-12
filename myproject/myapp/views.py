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
            return player_dashboard(request)
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
                else:
                    cursor = connection.cursor()
                    cursor.execute("SELECT * FROM Jury WHERE username = %s AND password = %s", [username, password])
                    user = cursor.fetchone()
                    if user:
                        return jury_dashboard(request)
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
            return render(request, 'admin_dashboard.html',  {'username': request.session.get('username')})
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT stadium_ID, stadium_name FROM Stadium")
            stadiums = cursor.fetchall()
        return render(request, 'update_stadium.html', {'stadiums': stadiums})


def coach_dashboard(request):
    with connection.cursor() as cursor:
        # Fetch jury details
        cursor.execute("SELECT username, name, surname FROM Jury")
        juries = cursor.fetchall()

        # Fetch stadium details
        cursor.execute("SELECT stadium_name, stadium_country FROM Stadium")
        stadiums = cursor.fetchall()

        context = {
            'juries': juries,
            'stadiums': stadiums,
            'username': request.session.get('username')
        }
        return render(request, 'coach_dashboard.html', context)


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
            print(result)
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
        player_usernames = request.POST.getlist('player_usernames')
        position_ids = request.POST.getlist('position_ids')
        
        if len(set(player_usernames)) != 6:
            messages.error(request, "You must select exactly 6 unique players to form a squad.")
            return redirect('create_squad')
        
        player_positions = zip(player_usernames, position_ids)
        current_team_id = fetch_current_team_id(request.session.get('username'))

        with connection.cursor() as cursor:
            # Check if the selected players are valid and part of the coach's team
            valid_players_sql = """
                SELECT pt.username
                FROM PlayerTeams pt
                JOIN PlayerPositions pp ON pt.username = pp.username
                WHERE pt.team = %s
            """
            cursor.execute(valid_players_sql, [current_team_id])
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
            # Fetch players and their possible positions
            players_sql = """
                SELECT pt.username, pp.position
                FROM PlayerTeams pt
                JOIN PlayerPositions pp ON pt.username = pp.username
                WHERE pt.team = %s
            """
            cursor.execute(players_sql, [fetch_current_team_id(request.session.get('username'))])
            players_data = cursor.fetchall()

            players = {}
            for username, position in players_data:
                if username not in players:
                    players[username] = []
                players[username].append(position)

        return render(request, 'create_squad.html', {'players': players, 'session_id': session_id})


def jury_dashboard(request):
    from django.utils import timezone
    with connection.cursor() as cursor:
        # Fetch the average rating and count of sessions rated by the logged-in jury
        cursor.execute("""
            SELECT AVG(rating) AS average_rating, COUNT(*) AS total_sessions
            FROM MatchSession
            WHERE assigned_jury_username = %s AND rating IS NOT NULL
        """, [request.session.get('username')])
        result = cursor.fetchone()
        average_rating = result[0] if result[0] else 0
        total_sessions = result[1]

        current_date = timezone.now().date().isoformat()
        cursor.execute("""
            SELECT session_ID, date, stadium_ID, team_ID
            FROM MatchSession
            WHERE assigned_jury_username = %s AND (rating IS NULL OR rating = 0) AND date < %s
        """, [request.session.get('username'), current_date])
        unrated_sessions = cursor.fetchall()

        context = {
            'average_rating': average_rating,
            'total_sessions': total_sessions,
            'unrated_sessions': unrated_sessions,
            'username': request.session.get('username')
        }
        return render(request, 'jury_dashboard.html', context)
    

from django.http import HttpResponseRedirect
def submit_rating(request):
    from django.utils import timezone
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        rating = request.POST.get('rating')

        with connection.cursor() as cursor:
            # Update the session rating
            cursor.execute("""
                UPDATE MatchSession
                SET rating = %s
                WHERE session_ID = %s AND assigned_jury_username = %s AND date < %s
            """, [rating, session_id, request.session.get('username'), timezone.now().date().isoformat()])
            
        return jury_dashboard(request)

    return jury_dashboard(request) 


def player_dashboard(request):
    from collections import Counter
    with connection.cursor() as cursor:
        # Fetch all players the logged-in player has played with
        cursor.execute("""
            SELECT p.name, p.surname
            FROM Player p
            JOIN SessionSquads sq ON p.username = sq.played_player_username
            WHERE sq.session_ID IN (
                SELECT session_ID
                FROM SessionSquads
                WHERE played_player_username = %s
            ) AND p.username != %s
            GROUP BY p.username
        """, [request.session.get('username'), request.session.get('username')])
        played_with_players = cursor.fetchall()

        # Fetch all session IDs where the logged-in player has played
        cursor.execute("""
            SELECT played_player_username
            FROM SessionSquads
            WHERE session_ID IN (
                SELECT session_ID
                FROM SessionSquads
                WHERE played_player_username = %s
            )
        """, [request.session.get('username')])
        all_playmates = [row[0] for row in cursor.fetchall()]

        # Calculate the most frequent playmate(s)
        playmate_counter = Counter(all_playmates)
        max_plays = playmate_counter.most_common(1)[0][1]
        most_frequent_playmates = [playmate for playmate, count in playmate_counter.items() if count == max_plays and playmate != request.session.get('username')]

        # Get height information for the most frequent playmate(s)
        cursor.execute("""
            SELECT AVG(height)
            FROM Player
            WHERE username IN %s
        """, [tuple(most_frequent_playmates)])
        average_height = cursor.fetchone()[0]

        context = {
            'played_with_players': played_with_players,
            'average_height': average_height,
            'username': request.session.get('username')
        }
        return render(request, 'player_dashboard.html', context)