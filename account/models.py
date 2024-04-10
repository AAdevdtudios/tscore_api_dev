from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .manager import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


AUTH_PROVIDERS = {
    "email": "email",
    "google": "google",
    "apple": "apple",
    "facebook": "facebook",
}


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        max_length=255, unique=True, verbose_name=_("Email Address")
    )
    first_name = models.CharField(max_length=255, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last Name"))
    phone_number = models.CharField(
        max_length=255, verbose_name=_("Phone Number"), blank=True, null=True
    )
    subscriber_number = models.CharField(
        max_length=255, unique=True, verbose_name=_("Subscriber Number")
    )
    is_subscribed = models.BooleanField(default=False, verbose_name=_("Subscribed"))
    subscriptionDate = models.DateTimeField(
        auto_now=True, verbose_name=_("Subscription Date")
    )
    nextSubscriptionDate = models.DateTimeField(
        auto_now=True, verbose_name=_("Next Date")
    )
    subscriptionCode = models.CharField(
        max_length=256, verbose_name=_("Subscription Code"), default="", blank=True
    )
    notification_id = models.CharField(max_length=256, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    email_token = models.CharField(blank=True, null=True, max_length=250)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    dateJoined = models.DateTimeField(auto_now_add=True)
    lastLogin = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(max_length=50, default=AUTH_PROVIDERS.get("email"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    def is_subscribed_change(self):
        if self.is_subscribed == False:
            return False
        if self.nextSubscriptionDate < timezone.now().date():
            self.is_subscribed = False
            return False
        self.is_subscribed = True
        return True


class OneTimePassword(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=6, unique=True)
    date = models.CharField(max_length=256)
    secrete = models.CharField(max_length=256)

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}-> pass code"
