from django.contrib import admin
from .models import SubscriptionPlans, Subscribers

# Register your models here.
admin.site.register(SubscriptionPlans)
admin.site.register(Subscribers)
