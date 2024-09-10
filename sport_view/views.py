from django.http import Http404 # type: ignore
from django.shortcuts import render, get_object_or_404 # type: ignore

from account.models import User


# Create your views here.
def game_table(request, pk: int):
    users = get_object_or_404(User, subscriber_number=pk)
    if not users.is_subscribed:
        raise Http404("User not subscribed")
    return render(request, "index.html", {})


def game_league(request, pk: int):
    users = get_object_or_404(User, subscriber_number=pk)
    if not users.is_subscribed:
        raise Http404("User not subscribed")
    return render(request, "league.html", {})


def game_live(request, pk: int):
    users = get_object_or_404(User, subscriber_number=pk)
    if not users.is_subscribed:
        raise Http404("User not subscribed")
    return render(request, "live.html", {})
