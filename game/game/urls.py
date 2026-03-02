from django.contrib import admin
from django.urls import path
from myapp import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Basic pages
    path("", views.index),

    # Authentication
    path("login/", views.login),
    path("user_register/", views.user_register),

    # Admin Dashboard
    path("admin_home/", views.admin_home),
    path("tc_home/", views.tc_index),

    # Tournament Constructor
    path("register_tc/", views.register_tc),
    path("tc_view_game/", views.tc_view_game),
    path("tc_view_team_requests/", views.tc_view_team_requests),
    path("tc_approve_team_request/", views.tc_approve_team_request),
    path("tc_reject_team_request/", views.tc_reject_team_request),
    path("tc_view_tournament/", views.tc_view_tournament),
    path("tc_view_registrations/", views.tc_view_registrations),
    path("tc_update_registration_status/", views.tc_update_registration_status),
    path("add_game/", views.add_game),
    path("add_tournament/", views.tc_add_tournament),
    path("add_match/", views.add_match),
    path("tc_view_matches/", views.tc_view_matches),
    path("edit_game/", views.tc_edit_game),
    path("edit_tournament/", views.edit_tournament),
    path("delete_game/", views.tc_delete_game),
    path("delete_tournament/", views.delete_tournament),
    path("update_match_result/", views.tc_update_match_result),
    
    
    # Games (Admin)

    # User Section
    path("user_home/", views.user_home),
    path("user_profile/", views.user_profile),
    path("user_profile/edit/", views.user_profile_edit),

    # Team Requests
    path("user_team_request/", views.user_team_request),
    path("user_team_requests/", views.user_team_requests),
    
    path("admin_view_users/", views.admin_view_users),
    path("admin_view_tc/", views.admin_view_tc),


    # Teams & Members
    path("user_view_teams/", views.user_view_teams),
    path("team_detail/", views.team_detail),
    path("add_team_member/", views.add_team_member),
    path("delete_team_member/", views.delete_team_member),

    # Tournaments (Admin)
    path("admin_view_tournament/", views.admin_view_tournament),
    

    # Tournament Registration
    path("user_view_tournaments/", views.user_view_tournaments),
    path("user_register_tournament/", views.user_register_tournament),
    path("user_view_matches/", views.user_view_matches),
    path("user_view_registrations/", views.user_view_registrations),


    # Feedback
    path("add_feedback/", views.add_feedback),
    path("view_feedback/", views.view_feedback),
    path("admin_view_feedback/", views.admin_view_feedback),
    path("reply_feedback/", views.reply_feedback),

  
]
