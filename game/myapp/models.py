from django.db import models
from django.contrib.auth.models import AbstractUser


# ----------------------------------------------------
# 1. Login (Admin / User)
# ----------------------------------------------------
class Login(AbstractUser):
   
    usertype = models.CharField(max_length=50,)
    viewpassword = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.usertype})"


# ----------------------------------------------------
# 2. Game (like Category in your example)
# ----------------------------------------------------
class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g. Valorant, BGMI
    description = models.TextField(blank=True, null=True)
    team_size = models.IntegerField(default=5)  # players per team
    status = models.IntegerField(default=1)  # 1=active, 0=inactive

    def __str__(self):
        return self.name


# ----------------------------------------------------
# 3. Player Profile (like UserProfile)
# ----------------------------------------------------
class PlayerProfile(models.Model):
    login = models.ForeignKey(Login, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    gamer_tag = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.IntegerField(default=1)  # 1=active, 0=blocked

    def __str__(self):
        return f"{self.gamer_tag} ({self.name})"
    
class TournamentConstructor(models.Model):
    loginid = models.ForeignKey(Login, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    profile_pic = models.ImageField(upload_to="tc_profiles/", blank=True, null=True)
    status = models.CharField(max_length=20, default="pending")  # pending / active / blocked

    def __str__(self):
        return f"{self.name} ({self.loginid.username})"



# ----------------------------------------------------
# 4. Team
# ----------------------------------------------------
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    captain = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='captain_teams'
    )
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)  # 1=active, 0=inactive

    def __str__(self):
        return self.name


# ----------------------------------------------------
# 5. Team Member (players inside a team)
# ----------------------------------------------------
class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, default='Player')
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)  # 1=active, 0=removed

    def __str__(self):
        name = self.player.gamer_tag if self.player else self.guest_name
        return f"{name} -> {self.team.name} ({self.role})"


# ----------------------------------------------------
# 6. Team Creation Request (user requests, admin accepts)
# ----------------------------------------------------
class TeamCreationRequest(models.Model):
    

    requested_by = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_request_logos/', blank=True, null=True)
    reason = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20,  default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # optional: link to created Team after approval
    created_team = models.OneToOneField(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.team_name} ({self.status})"

from django.contrib.auth import get_user_model
# ----------------------------------------------------
# 7. Tournament (admin can add & manage tournaments)
# ----------------------------------------------------
class Tournament(models.Model):
    name = models.CharField(max_length=150)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, default='Upcoming')

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_open_at = models.DateTimeField()
    registration_close_at = models.DateTimeField()

    max_teams = models.IntegerField(default=16)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prize_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_online = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Add this field to track which TC created the tournament
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,  # optional for existing tournaments
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.game.name}"


# ----------------------------------------------------
# 8. Tournament Registration (Team joins tournament)
# ----------------------------------------------------
class TournamentRegistration(models.Model):
    

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, default='Pending')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tournament', 'team')

    def __str__(self):
        return f"{self.team.name} in {self.tournament.name} ({self.status})"


# ----------------------------------------------------
# 9. Match (admin adds matchups)
# ----------------------------------------------------
class Match(models.Model):
    

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')

    round_name = models.CharField(max_length=50, blank=True, null=True)  # e.g. Quarter Final
    scheduled_at = models.DateTimeField()

    status = models.CharField(max_length=20,  default='Scheduled')

    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wins'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tournament.name}: {self.team1.name} vs {self.team2.name}"


# ----------------------------------------------------
# 10. Feedback (user adds, admin views & replies)
# ----------------------------------------------------
class Feedback(models.Model):
    user = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True, blank=True)

    rating = models.IntegerField(default=0)  # 1–5
    subject = models.CharField(max_length=100)
    message = models.TextField()

    admin_reply = models.TextField(blank=True, null=True)
    reply_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.gamer_tag} for {self.tournament}"
