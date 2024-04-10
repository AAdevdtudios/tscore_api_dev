from rest_framework import serializers
from .models import SubscriptionPlans, Subscribers


class SubscribePlan(serializers.Serializer):
    planName = serializers.CharField(max_length=68)


class WebhookData(serializers.Serializer):
    subscription_code = serializers.CharField(max_length=256)
    next_payment_date = serializers.CharField(max_length=256, required=False)


class WebhookResponse(serializers.ModelSerializer):
    class Meta:
        model = Subscribers
        fields = "__all__"
