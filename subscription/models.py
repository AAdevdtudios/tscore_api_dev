from typing import Any
from django.db import models
from django.conf import settings
from logics.utils import CreatePlan

User = settings.AUTH_USER_MODEL

SUBSCRIPTIONTYPE = {
    "silver": "silver",
    "gold": "gold",
    "premium": "premium",
    "diamond": "diamond",
}
GENRE_CHOICES = (
    ("active", "Active"),
    ("deactivate", "Deactivate"),
    ("no_renew", "No_Renew"),
)
INTERVAL_TYPE = (
    ("hourly", "hourly"),
    ("daily", "daily"),
    ("weekly", "weekly"),
    ("monthly", "monthly"),
    ("quarterly", "quarterly"),
    ("biannually", "biannually"),
    ("annually", "annually"),
)


# Create your models here.
class SubscriptionPlans(models.Model):
    PlanType = models.CharField(max_length=50, default=SUBSCRIPTIONTYPE.get("silver"))
    PlanCode = models.CharField(max_length=256, blank=True, null=True)
    Price = models.IntegerField()
    PlaneName = models.CharField(max_length=256, blank=True, null=True)
    interval = models.CharField(max_length=20, choices=INTERVAL_TYPE, default="hourly")

    class Meta:
        verbose_name = "SubscriptionPlan"
        verbose_name_plural = "SubscriptionPlans"

    def save(self, *args, **kwargs):
        data = CreatePlan(
            amount=self.Price * 100, name=self.PlaneName, interval=self.interval
        )
        self.PlanCode = data
        super(SubscriptionPlans, self).save(
            *args, **kwargs
        )  # Call the real save() method

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.PlanCode


class Subscribers(models.Model):
    subscription_code = models.CharField(max_length=256)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=20, choices=GENRE_CHOICES)

    class Meta:
        verbose_name = "Subscriber"
        verbose_name_plural = "Subscribers"

    def __str__(self) -> str:
        return self.subscription_code
