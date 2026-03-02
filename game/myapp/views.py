from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.db import IntegrityError
from .models import *


# ------------------------------------------------
# Basic Pages
# ------------------------------------------------
def index(request):
    return render(request, "index.html")



def tc_index(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        return redirect("/login/")
    
    # TC Dashboard Stats
    total_games = Game.objects.count()
    total_tournaments = Tournament.objects.filter(created_by=request.user).count()
    pending_team_requests = TeamCreationRequest.objects.filter(status="Pending").count()
    pending_registrations = TournamentRegistration.objects.filter(tournament__created_by=request.user, status="Pending").count()

    context = {
        "total_games": total_games,
        "total_tournaments": total_tournaments,
        "pending_team_requests": pending_team_requests,
        "pending_registrations": pending_registrations,
    }
    return render(request, "TOURNAMENT/index.html", context)




# ------------------------------------------------
# 1. Login / Logout
# ------------------------------------------------
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            auth_login(request, user)

            # admin
            if user.is_superuser or user.is_staff or user.usertype == "admin":
                messages.success(request, "Login successful (admin)")
                return redirect("/admin_home/")

            # normal gamer/user
            elif user.usertype == "user":
                request.session["user_id"] = user.id
                messages.success(request, "Login successful (user)")
                return redirect("/user_home/")

            # Tournament Constructor
            elif user.usertype == "tournament_constructor":
                request.session["tc_id"] = user.id  # separate session key
                messages.success(request, "Login successful (Tournament Constructor)")
                return redirect("/tc_home/")  # redirect to their dashboard

            else:
                messages.error(request, "User type not allowed.")
                return render(request, "login.html")

        else:
            messages.error(request, "Invalid username or password")
            return render(request, "login.html")

    return render(request, "login.html")



def register_tc(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        name = request.POST.get("name")
        profile_pic = request.FILES.get("profile_pic")

        # Check if username/email already exists
        if Login.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("/register_tc/")

        # Create Login object
        login_obj = Login.objects.create_user(
            username=username,
            password=password,
            usertype="tournament_constructor",
            viewpassword=password
        )

        # Create TournamentConstructor profile (similar to Staff)
        TournamentConstructor.objects.create(
            loginid=login_obj,
            name=name,
            email=email,
            phone=phone,
            profile_pic=profile_pic,
            status="pending"
        )

        messages.success(request, "Tournament Constructor registered successfully.")
        return redirect("/login/")

    return render(request, "tc_register.html")


def user_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        gamer_tag = request.POST.get("gamer_tag")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        game_id = request.POST.get("game")  # optional

        # Check passwords
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("/user_register/")

        # Check if username/email already exists
        if Login.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return redirect("/user_register/")

        # Check if phone or gamer_tag already exists
        if PlayerProfile.objects.filter(phone=phone).exists():
            messages.error(request, "Phone already registered")
            return redirect("/user_register/")
        if PlayerProfile.objects.filter(gamer_tag=gamer_tag).exists():
            messages.error(request, "Gamer tag already taken")
            return redirect("/user_register/")

        # Create Login first
        login_obj = Login.objects.create_user(
            username=email,
            password=password,
            usertype="user",
            viewpassword=password
        )

        # Get optional game
        game = Game.objects.filter(id=game_id).first() if game_id else None

        # Create PlayerProfile safely
        try:
            PlayerProfile.objects.create(
                login=login_obj,
                name=name,
                email=email,
                phone=phone,
                gamer_tag=gamer_tag,
                address=address,
                game=game,
                status=1
            )
        except IntegrityError as e:
            # Delete login if profile creation fails
            login_obj.delete()
            messages.error(request, f"Failed to create profile: {str(e)}")
            return redirect("/user_register/")

        messages.success(request, "Registration successful. Please login.")
        return redirect("/login/")

    # GET request: show registration form
    games = Game.objects.filter(status=1)
    return render(request, "user_reg.html", {"games": games})


# ------------------------------------------------
# 3. Admin Home / Dashboard
# ------------------------------------------------
def admin_home(request):
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    players = PlayerProfile.objects.all()
    teams = Team.objects.all()
    tournaments = Tournament.objects.all()
    team_requests = TeamCreationRequest.objects.filter(status="Pending")

    context = {
        "players": players,
        "teams": teams,
        "tournaments": tournaments,
        "total_players": players.count(),
        "total_teams": teams.count(),
        "total_tournaments": tournaments.count(),
        "pending_team_requests": team_requests.count(),
    }
    return render(request, "ADMIN/index.html", context)

def admin_view_users(request):
    # Admin check
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    users = PlayerProfile.objects.select_related("login", "game").all().order_by("-id")
    return render(request, "ADMIN/view_users.html", {"users": users})


def admin_view_tc(request):
    # Admin check
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    tcs = TournamentConstructor.objects.select_related("loginid").all().order_by("-id")
    return render(request, "ADMIN/view_tc.html", {"tcs": tcs})


# ------------------------------------------------
# 4. Game Management (Tournament Constructor)
# ------------------------------------------------
def add_game(request):
    # tournament constructor check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        team_size = request.POST.get("team_size", "").strip()

        if name == "":
            messages.error(request, "Game name cannot be empty.")
            return render(request, "TOURNAMENT/add_game.html")

        if Game.objects.filter(name__iexact=name).exists():
            messages.error(request, "Game already exists.")
            return render(request, "TOURNAMENT/add_game.html")

        try:
            tsize = int(team_size) if team_size else 5
        except ValueError:
            tsize = 5

        Game.objects.create(
            name=name,
            description=description,
            team_size=tsize,
            status=1,
        )

        messages.success(request, "Game added successfully")
        return redirect("/tc_view_game/")  # redirect to TC view page

    return render(request, "TOURNAMENT/add_game.html")

# def admin_view_game(request):
#     # Admin check
#     if not request.user.is_authenticated or (
#         not request.user.is_superuser
#         and not request.user.is_staff
#         and request.user.usertype != "admin"
#     ):
#         messages.error(request, "Admin login required.")
#         return redirect("/login/")
#
#     games = Game.objects.all().order_by("-id")
#     return render(request, "ADMIN/view_game.html", {"games": games})


def tc_view_game(request):
    # Tournament Constructor check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    games = Game.objects.all().order_by("-id")
    return render(request, "TOURNAMENT/tc_view_game.html", {"games": games})


def tc_edit_game(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    id = request.GET.get("id")
    game = Game.objects.filter(id=id).first()

    if not game:
        messages.error(request, "Game not found")
        return redirect("/tc_view_game/")

    if request.method == "POST":
        game.name = request.POST.get("name", game.name).strip()
        game.description = request.POST.get("description", game.description).strip()
        try:
            game.team_size = int(request.POST.get("team_size", game.team_size))
        except ValueError:
            pass
        game.save()
        messages.success(request, "Game updated")
        return redirect("/tc_view_game/")

    return render(request, "TOURNAMENT/edit_game.html", {"game": game})


def tc_delete_game(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    id = request.GET.get("id")
    game = Game.objects.filter(id=id).first()

    if game:
        game.delete()
        messages.success(request, "Game deleted successfully")
    else:
        messages.error(request, "Game not found")
    return redirect("/tc_view_game/")


# ------------------------------------------------
# 5. User Home + Profile
# ------------------------------------------------
def user_home(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    profile = PlayerProfile.objects.filter(login_id=user_id).first()
    if not profile:
        messages.error(request, "Player profile not found")
        return redirect("/login/")

    # Dashboard Stats
    team_count = Team.objects.filter(captain=profile).count()
    registration_count = TournamentRegistration.objects.filter(team__captain=profile).count()
    
    # Matches count (involved teams)
    user_teams = Team.objects.filter(captain=profile)
    match_count = Match.objects.filter(
        models.Q(team1__in=user_teams) | models.Q(team2__in=user_teams)
    ).count()

    context = {
        "profile": profile,
        "team_count": team_count,
        "registration_count": registration_count,
        "match_count": match_count,
    }
    return render(request, "USER/index.html", context)

def user_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/login/")

    # Use 'login' FK correctly
    profile = PlayerProfile.objects.filter(login__id=user_id).first()
    return render(request, "USER/user_profile.html", {"profile": profile})


def user_profile_edit(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/login/")

    profile = PlayerProfile.objects.filter(login__id=user_id).first()
    games = Game.objects.filter(status=1)
    
    # Pre-calculate selected status to avoid template syntax issues
    for g in games:
        g.is_selected = (profile.game_id == g.id) if profile and profile.game else False

    if request.method == "POST" and profile:
        profile.name = request.POST.get("name")
        profile.phone = request.POST.get("phone")
        profile.address = request.POST.get("address")
        game_id = request.POST.get("game")
        if game_id:
            profile.game_id = game_id
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("/user_profile/")

    return render(request, "USER/edit_profile.html", {"profile": profile, "games": games})



# ------------------------------------------------
# 6. Team Creation Request (User) + Admin Actions
# ------------------------------------------------
def user_team_request(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    if not player:
        messages.error(request, "Player profile not found")
        return redirect("/login/")

    if request.method == "POST":
        team_name = request.POST.get("team_name", "").strip()
        reason = request.POST.get("reason", "").strip()
        logo = request.FILES.get("logo")

        if team_name == "":
            messages.error(request, "Team name cannot be empty")
            return render(request, "USER/team_request.html")

        if Team.objects.filter(name__iexact=team_name).exists():
            messages.error(request, "Team name already exists")
            return render(request, "USER/team_request.html")

        members_list = request.POST.get("members_list", "").strip()
        full_reason = f"{reason}\n\nProposed Members:\n{members_list}" if members_list else reason

        TeamCreationRequest.objects.create(
            requested_by=player,
            team_name=team_name,
            logo=logo,
            reason=full_reason,
            status="Pending",
        )

        messages.success(request, "Team creation request submitted")
        return redirect("/user_team_requests/")

    return render(request, "USER/team_request.html")


def user_team_requests(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    requests_list = TeamCreationRequest.objects.filter(requested_by=player).order_by("-created_at")

    return render(request, "USER/view_team_requests.html", {"requests": requests_list})


def tc_view_team_requests(request):
    # Tournament Constructor check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    requests_list = TeamCreationRequest.objects.all().order_by("-created_at")
    return render(request, "TOURNAMENT/view_team_requests.html", {"requests": requests_list})


def tc_approve_team_request(request):
    # Tournament Constructor check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    id = request.GET.get("id")
    tr = TeamCreationRequest.objects.filter(id=id).first()

    if not tr:
        messages.error(request, "Request not found")
        return redirect("/tc_view_team_requests/")

    if tr.status == "Approved":
        messages.info(request, "Already approved")
        return redirect("/tc_view_team_requests/")

    # Create Team
    team = Team.objects.create(
        name=tr.team_name,
        captain=tr.requested_by,
        logo=tr.logo,
        status=1,
    )

    # Add captain as TeamMember
    TeamMember.objects.create(
        team=team,
        player=tr.requested_by,
        role="Captain",
        status=1,
    )

    tr.status = "Approved"
    tr.created_team = team
    tr.save()

    messages.success(request, "Team created and request approved")
    return redirect("/tc_view_team_requests/")


def tc_reject_team_request(request):
    # Tournament Constructor check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    id = request.GET.get("id")
    tr = TeamCreationRequest.objects.filter(id=id).first()

    if tr:
        tr.status = "Rejected"
        tr.save()
        messages.success(request, "Team request rejected")
    else:
        messages.error(request, "Request not found")

    return redirect("/tc_view_team_requests/")


# ------------------------------------------------
# 7. Team View / Members (User)
# ------------------------------------------------
def user_view_teams(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    if not player:
        messages.error(request, "Player profile not found")
        return redirect("/login/")

    # Teams where user is captain
    captain_teams = Team.objects.filter(captain=player).prefetch_related(
        'teammember_set__player'
    ).order_by("-id")
    
    # Teams where user is a member
    member_memberships = TeamMember.objects.filter(player=player, status=1).select_related('team')
    member_teams_ids = [m.team.id for m in member_memberships]
    member_teams = Team.objects.filter(id__in=member_teams_ids).prefetch_related(
        'teammember_set__player'
    )

    return render(request, "USER/view_teams.html", {"teams": captain_teams, "member_teams": member_teams})


def team_detail(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    id = request.GET.get("id")

    team = Team.objects.filter(id=id).first()
    
    if not team:
         messages.error(request, "Team not found")
         return redirect("/user_view_teams/")

    # Check if captain or member
    is_captain = (team.captain.id == player.id)
    is_member = TeamMember.objects.filter(team=team, player=player, status=1).exists()

    if not is_captain and not is_member:
        messages.error(request, "You are not a member of this team")
        return redirect("/user_view_teams/")

    members = TeamMember.objects.filter(team=team, status=1)
    return render(request, "USER/team_detail.html", {
        "team": team, 
        "members": members, 
        "is_captain": is_captain
    })


def add_team_member(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    team_id = request.GET.get("team_id") or request.POST.get("team_id")
    team = Team.objects.filter(id=team_id, captain=player).first()

    if not team:
        messages.error(request, "Team not found or you are not the captain")
        return redirect("/user_view_teams/")

    if request.method == "POST":
        gamer_tag = request.POST.get("gamer_tag", "").strip()
        role = request.POST.get("role", "Player").strip()

        if gamer_tag == "":
            messages.error(request, "Gamer tag is required")
            return redirect(f"/team_detail/?id={team.id}")

        member_player = PlayerProfile.objects.filter(gamer_tag=gamer_tag).first()

        if member_player:
            # Add registered player
            tm, created = TeamMember.objects.get_or_create(
                team=team,
                player=member_player,
                defaults={"role": role, "status": 1},
            )
            if not created:
                if tm.status == 0:
                    tm.status = 1
                    tm.role = role
                    tm.save()
                    messages.success(request, f"Member '{gamer_tag}' re-added to team")
                else:
                    messages.info(request, f"Player '{gamer_tag}' already in the team")
            else:
                messages.success(request, f"Member '{gamer_tag}' added to team")
        else:
            # Handle as Guest Member
            tm = TeamMember.objects.filter(team=team, guest_name=gamer_tag).first()
            if tm:
                if tm.status == 0:
                    tm.status = 1
                    tm.role = role
                    tm.save()
                    messages.success(request, f"Guest '{gamer_tag}' re-added to team")
                else:
                    messages.info(request, f"Guest '{gamer_tag}' already in the team")
            else:
                TeamMember.objects.create(
                    team=team,
                    guest_name=gamer_tag,
                    role=role,
                    status=1
                )
                messages.success(request, f"Guest '{gamer_tag}' added to team")

        return redirect(f"/team_detail/?id={team.id}")

    return render(request, "USER/add_team_member.html", {"team": team})


def delete_team_member(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    id = request.GET.get("id")
    tm = TeamMember.objects.filter(id=id, team__captain=player).first()

    if tm:
        tm.status = 0  # soft delete
        tm.save()
        messages.success(request, "Member removed from team")
        return redirect(f"/team_detail/?id={tm.team.id}")
    else:
        messages.error(request, "Team member not found")
        return redirect("/user_view_teams/")

# ------------------------------------------------
# 8. Tournament Management (Tournament Constructor)
# ------------------------------------------------
def tc_add_tournament(request):
    # TC check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    if request.method == "POST":
        name = request.POST.get("name")
        game_id = request.POST.get("game")
        description = request.POST.get("description")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        registration_open_at = request.POST.get("registration_open_at")
        registration_close_at = request.POST.get("registration_close_at")
        max_teams = request.POST.get("max_teams") or 16
        entry_fee = request.POST.get("entry_fee") or 0
        prize_pool = request.POST.get("prize_pool") or 0
        is_online = request.POST.get("is_online") == "on"
        location = request.POST.get("location")

        game = Game.objects.get(id=game_id)

        Tournament.objects.create(
            name=name,
            game=game,
            description=description,
            start_date=start_date,
            end_date=end_date,
            registration_open_at=registration_open_at,
            registration_close_at=registration_close_at,
            max_teams=max_teams,
            entry_fee=entry_fee,
            prize_pool=prize_pool,
            is_online=is_online,
            location=location,
            created_by=request.user  # ✅ THIS FIXES EVERYTHING
        )

        messages.success(request, "Tournament added successfully")
        return redirect("/tc_view_tournament/")

    games = Game.objects.filter(status=1)
    return render(request, "TOURNAMENT/add_tournament.html", {"games": games})





def tc_view_tournament(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    tournaments = Tournament.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    return render(
        request,
        "TOURNAMENT/view_tournament.html",
        {"tournaments": tournaments}
    )


def edit_tournament(request):
    # Tournament Constructor (TC) check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    tournament_id = request.GET.get("id")
    tournament = Tournament.objects.filter(id=tournament_id, created_by=request.user).first()

    if not tournament:
        messages.error(request, "Tournament not found")
        return redirect("/tc_view_tournament/")

    if request.method == "POST":
        tournament.name = request.POST.get("name", tournament.name)
        tournament.description = request.POST.get("description", tournament.description)
        tournament.status = request.POST.get("status", tournament.status)
        tournament.start_date = request.POST.get("start_date") or tournament.start_date
        tournament.end_date = request.POST.get("end_date") or tournament.end_date
        tournament.registration_open_at = request.POST.get("registration_open_at") or tournament.registration_open_at
        tournament.registration_close_at = request.POST.get("registration_close_at") or tournament.registration_close_at
        
        # Convert numeric fields safely
        try:
            tournament.max_teams = int(request.POST.get("max_teams", tournament.max_teams))
        except ValueError:
            pass

        try:
            tournament.entry_fee = float(request.POST.get("entry_fee", tournament.entry_fee))
        except ValueError:
            pass

        try:
            tournament.prize_pool = float(request.POST.get("prize_pool", tournament.prize_pool))
        except ValueError:
            pass

        tournament.is_online = request.POST.get("is_online") == "on"
        tournament.location = request.POST.get("location", tournament.location)
        tournament.save()

        messages.success(request, "Tournament updated successfully")
        return redirect("/tc_view_tournament/")

    games = Game.objects.filter(status=1)  # only active games
    return render(
        request,
        "TOURNAMENT/edit_tournament.html",
        {"tournament": tournament, "games": games},
    )


def delete_tournament(request):
    # Tournament Constructor (TC) check
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    tournament_id = request.GET.get("id")
    tournament = Tournament.objects.filter(id=tournament_id, created_by=request.user).first()

    if tournament:
        tournament.delete()
        messages.success(request, "Tournament deleted successfully")
    else:
        messages.error(request, "Tournament not found")

    return redirect("/tc_view_tournament/")



def admin_view_tournament(request):
    # Admin check
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    tournaments = Tournament.objects.all().order_by("-created_at")
    return render(request, "ADMIN/view_tournament.html", {"tournaments": tournaments})


# ------------------------------------------------
# 9. Tournament Registration (User)
# ------------------------------------------------
def user_view_tournaments(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    tournaments = Tournament.objects.all().order_by("start_date")
    now = datetime.now()
    return render(request, "USER/view_tournaments.html", {"tournaments": tournaments, "now": now})


def user_view_matches(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    tournament_id = request.GET.get("tournament_id")
    tournament = Tournament.objects.filter(id=tournament_id).first()
    
    if tournament:
        matches = Match.objects.filter(tournament=tournament).order_by("scheduled_at")
    else:
        # Show all matches for tournaments the user is involved in
        player = PlayerProfile.objects.filter(login_id=user_id).first()
        user_teams = Team.objects.filter(captain=player)
        matches = Match.objects.filter(
            models.Q(team1__in=user_teams) | models.Q(team2__in=user_teams)
        ).order_by("-scheduled_at")

    return render(request, "USER/view_matches.html", {"matches": matches, "tournament": tournament})


def user_view_registrations(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    user_teams = Team.objects.filter(captain=player)
    
    registrations = TournamentRegistration.objects.filter(
        team__in=user_teams
    ).order_by("-registered_at")

    return render(request, "USER/view_registrations.html", {"registrations": registrations})


def user_register_tournament(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    if not player:
        messages.error(request, "Player profile not found")
        return redirect("/login/")

    tid = request.GET.get("id") or request.POST.get("tournament_id")
    tournament = Tournament.objects.filter(id=tid).first()

    if not tournament:
        messages.error(request, "Tournament not found")
        return redirect("/user_view_tournaments/")

    teams = Team.objects.filter(captain=player, status=1)

    if request.method == "POST":
        team_id = request.POST.get("team_id")
        team = Team.objects.filter(id=team_id, captain=player).first()

        if not team:
            messages.error(request, "Team not found")
            return redirect(f"/user_register_tournament/?id={tournament.id}")

        if TournamentRegistration.objects.filter(tournament=tournament, team=team).exists():
            messages.info(request, "This team is already registered for this tournament")
            return redirect("/user_view_tournaments/")

        # Default payment status
        pay_status = "Pending"
        if tournament.entry_fee == 0:
            pay_status = "Not Required"

        reg = TournamentRegistration.objects.create(
            tournament=tournament,
            team=team,
            status="Pending",
            payment_status=pay_status
        )

        if tournament.entry_fee > 0:
            return redirect(f"/tournament_payment/?reg_id={reg.id}")

        messages.success(request, "Registration submitted")
        return redirect("/user_view_tournaments/")

    return render(
        request,
        "USER/register_tournament.html",
        {"tournament": tournament, "teams": teams},
    )


def tournament_payment(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/login/")

    reg_id = request.GET.get("reg_id")
    reg = TournamentRegistration.objects.filter(id=reg_id, team__captain__login_id=user_id).first()

    if not reg:
        messages.error(request, "Registration record not found.")
        return redirect("/user_view_tournaments/")

    if request.method == "POST":
        # Mock payment processing
        reg.payment_status = "Paid"
        reg.payment_id = request.POST.get("card_number")[-4:] + "-MOCK-" + os.urandom(4).hex()
        reg.save()
        messages.success(request, f"Payment successful! Fee: {reg.tournament.entry_fee}")
        return redirect("/user_view_tournaments/")

    return render(request, "USER/tournament_payment.html", {"reg": reg})



# ------------------------------------------------
# 11. Feedback (User + Admin)
# ------------------------------------------------
def add_feedback(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()

    tid = request.GET.get("tournament_id") or request.POST.get("tournament_id")
    tournament = Tournament.objects.filter(id=tid).first()

    if not tournament:
        messages.error(request, "Tournament not found.")
        return redirect("/user_view_tournaments/")

    if request.method == "POST":
        rating = request.POST.get("rating")
        subject = request.POST.get("subject")
        message_txt = request.POST.get("message")

        Feedback.objects.create(
            user=player,
            tournament=tournament,
            rating=rating,
            subject=subject,
            message=message_txt,
        )

        messages.success(request, "Feedback submitted")
        return redirect("/view_feedback/")

    return render(request, "USER/add_feedback.html", {"tournament": tournament})


def view_feedback(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("/login/")

    player = PlayerProfile.objects.filter(login_id=user_id).first()
    feedbacks = Feedback.objects.filter(user=player).order_by("-created_at")
    return render(request, "USER/view_feedback.html", {"feedbacks": feedbacks})


def admin_view_feedback(request):
    # Admin check
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    feedbacks = Feedback.objects.select_related("user", "tournament").all().order_by("-created_at")
    return render(request, "ADMIN/view_feedback_admin.html", {"feedbacks": feedbacks})


# ------------------------------------------------
# 12. Registration Management (TC)
# ------------------------------------------------

def tc_view_registrations(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    # View registrations for tournaments created by this TC
    registrations = TournamentRegistration.objects.filter(
        tournament__created_by=request.user
    ).order_by("-registered_at")

    return render(request, "TOURNAMENT/view_registrations.html", {"registrations": registrations})


def tc_update_registration_status(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    reg_id = request.GET.get("id")
    status = request.GET.get("status") # 'Approved' or 'Rejected'
    
    registration = TournamentRegistration.objects.filter(
        id=reg_id, 
        tournament__created_by=request.user
    ).first()

    if registration:
        registration.status = status
        registration.save()
        messages.success(request, f"Registration {status.lower()} successfully.")
    else:
        messages.error(request, "Registration not found.")

    return redirect("/tc_view_registrations/")


# ------------------------------------------------
# 13. Match Management (TC)
# ------------------------------------------------

def tc_view_matches(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    matches = Match.objects.filter(
        tournament__created_by=request.user
    ).order_by("-scheduled_at")

    return render(request, "TOURNAMENT/view_matches.html", {"matches": matches})


def add_match(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    if request.method == "POST":
        tournament_id = request.POST.get("tournament")
        team1_id = request.POST.get("team1")
        team2_id = request.POST.get("team2")
        scheduled_at = request.POST.get("scheduled_at")
        round_name = request.POST.get("round_name")

        if team1_id == team2_id:
            messages.error(request, "Team 1 and Team 2 cannot be the same.")
            return redirect("/add_match/")

        tournament = Tournament.objects.get(id=tournament_id)
        team1 = Team.objects.get(id=team1_id)
        team2 = Team.objects.get(id=team2_id)

        Match.objects.create(
            tournament=tournament,
            team1=team1,
            team2=team2,
            scheduled_at=scheduled_at,
            round_name=round_name,
            status="Scheduled"
        )

        messages.success(request, "Match added successfully")
        return redirect("/tc_view_matches/")

    tournaments = Tournament.objects.filter(created_by=request.user)
    # Only show teams that are approved for some tournament of this TC
    # or just show all active teams for simplicity in this step
    teams = Team.objects.filter(status=1)
    
    return render(request, "TOURNAMENT/add_match.html", {
        "tournaments": tournaments,
        "teams": teams
    })


def tc_update_match_result(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")

    match_id = request.GET.get("id") or request.POST.get("match_id")
    match = Match.objects.filter(id=match_id, tournament__created_by=request.user).first()

    if not match:
        messages.error(request, "Match not found.")
        return redirect("/tc_view_matches/")

    if request.method == "POST":
        match.team1_score = request.POST.get("team1_score", 0)
        match.team2_score = request.POST.get("team2_score", 0)
        winner_id = request.POST.get("winner")
        match.status = "Completed"
        
        if winner_id:
            match.winner_id = winner_id
        
        match.save()
        messages.success(request, "Match result updated.")
        return redirect("/tc_view_matches/")

    return render(request, "TOURNAMENT/update_match.html", {"match": match})


def reply_feedback(request):
    # Admin check
    if not request.user.is_authenticated or (
        not request.user.is_superuser
        and not request.user.is_staff
        and request.user.usertype != "admin"
    ):
        messages.error(request, "Admin login required.")
        return redirect("/login/")

    feedback_id = request.GET.get("id")
    feedback = Feedback.objects.filter(id=feedback_id).first()

    if not feedback:
        messages.error(request, "Feedback not found.")
        return redirect("/admin_view_feedback/")

    if request.method == "POST":
        reply = request.POST.get("admin_reply")
        feedback.admin_reply = reply
        feedback.reply_date = datetime.now()
        feedback.save()
        messages.success(request, "Reply sent successfully.")
        return redirect("/admin_view_feedback/")

    return render(request, "ADMIN/reply_feedback.html", {"feedback": feedback})


# ------------------------------------------------
# 14. Tournament Constructor Profile
# ------------------------------------------------

def tc_profile(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")
    
    profile = TournamentConstructor.objects.filter(loginid=request.user).first()
    return render(request, "TOURNAMENT/tc_profile.html", {"profile": profile})


def tc_profile_edit(request):
    if not request.user.is_authenticated or request.user.usertype != "tournament_constructor":
        messages.error(request, "Tournament Constructor login required.")
        return redirect("/login/")
    
    profile = TournamentConstructor.objects.filter(loginid=request.user).first()

    if request.method == "POST" and profile:
        profile.name = request.POST.get("name")
        profile.phone = request.POST.get("phone")
        
        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES.get("profile_pic")
            
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("/tc_profile/")

    return render(request, "TOURNAMENT/edit_profile.html", {"profile": profile})
