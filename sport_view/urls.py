from django.urls import path
from .views import game_league, game_live, game_table

urlpatterns = [
    path("<int:pk>/", game_table, name="GameView"),
    path("live/<int:pk>/", game_live, name="LiveGame"),
    path("league/<int:pk>/", game_league, name="LeagueGame"),
]
