from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("game/", include("sport_view.urls")),
    path("admin/custom_view", include("notifications.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/", include("subscription.urls")),
    path("api/v1/auth/", include("account.urls")),
    path("api/v1/auth/", include("social_media.urls")),
]
