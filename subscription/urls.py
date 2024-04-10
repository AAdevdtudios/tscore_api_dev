from django.urls import path
from .views import (
    CreateSubscription,
    WebHookListener,
    CancelSubscription,
    UpdateUserSub,
)

urlpatterns = [
    path("subscribe/", view=CreateSubscription.as_view(), name="Create Subscription"),
    path("disable/", CancelSubscription.as_view(), name="disableSub"),
    path("updateSub/", UpdateUserSub.as_view(), name="updateSub"),
    path(
        "webhook-listener/", view=WebHookListener.as_view(), name="Transaction Listener"
    ),
]
