from .models import SubscriptionPlans
from account.serializer import ErrorValidation
from django.conf import settings
import requests
from .serializer import WebhookData
from datetime import datetime, date
from account.models import User
from .models import Subscribers

from paystackapi.paystack import Paystack

paystack_secret_key = settings.PAYSTACKSCKEY
paystack = Paystack(secret_key=paystack_secret_key)


def CheckReference(ref: str):
    data = paystack.subscription.list()
    return data


def CreatePlan(interval: str, name: str, amount: int):
    data = {"name": name, "interval": interval, "amount": amount}
    res = paystack.plan.create(data)
    if res in None:
        return "Unsaved"
    return res["data"]["plan_code"]


def UpdateSubscription(owner: User):
    code = owner.subscriptionCode
    response = requests.get(
        f"https://api.paystack.co/subscription/{code}/manage/link",
        headers={
            "Authorization": f"Bearer {paystack_secret_key}",
        },
    )
    if response.status_code != 200:
        raise ErrorValidation("Error")
    data = response.json()
    return data["data"]["link"]


def DisabledSubscription(owner: User):
    data = {
        "code": owner.subscriptionCode,
        "token": owner.email_token,
    }
    try:
        paystack.subscription.disable(**data)
    except Exception as ex:
        print(ex)


def SubscribeUser(email: str, planName: str):
    if SubscriptionPlans.objects.filter(PlanType=planName).exists():
        subscription = SubscriptionPlans.objects.get(PlanType=planName)
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers={"Authorization": "Bearer " + paystack_secret_key},
            data={
                "email": email,
                "amount": subscription.Price,
                "plan": subscription.PlanCode,
            },
        )
        if response.status_code == 400:
            raise ErrorValidation("Failed to connect", 400)
        data = response.json()
        print(data)
        return data["data"]["authorization_url"]
    raise ErrorValidation("This is serious", 400)


# invoice.create invoice.payment_failed invoice.update subscription.create subscription.disable subscription.not_renew charge.success
def EventActions(event, data):
    if event == "subscription.create":
        _subscriptionService(data=data)
        return "Subscription create"
    if event == "subscription.disable":
        _disableSubscription(data)
        return event
    if event == "invoice.create":
        _onRenew(data)
        return event
    if event == "invoice.payment_failed":
        return event
    if event == "invoice.update":
        return event
    if event == "subscription.not_renew":
        _notRenew(data)
        return event
    if event == "charge.success":
        return event
    return "Not created"


def _onRenew(data):
    email = data["data"]["customer"]["email"]
    try:
        user = User.objects.get(email=email)
        user.is_subscribed = True
    except User.DoesNotExist:
        return True


def _notRenew(data):
    try:
        code = Subscribers.objects.get(
            subscription_code=data["data"]["subscription_code"]
        )
        code.status = "no_renew"
        code.save()
        return True
    except:
        return False


def _disableSubscription(data):
    email = data["data"]["customer"]["email"]
    try:
        user = User.objects.get(email=email)
        user.is_subscribed = False
        user.save()
        return False
    except User.DoesNotExist:
        return False


def _subscriptionService(data):
    info = {
        "email": data["data"]["customer"]["email"],
        "subscription_code": data["data"]["subscription_code"],
    }

    try:
        if User.objects.filter(subscriptionCode=info["subscription_code"]).exists():
            return True
        user = User.objects.get(email=info["email"])
        if Subscribers.objects.filter(user=user).exists():
            code = Subscribers.objects.get(user=user)
            code.subscription_code = info["subscription_code"]
            code.save()
        else:
            code = Subscribers.objects.get(subscription_code=info["subscription_code"])
        user.subscriptionCode = code.subscription_code
        user.email_token = data["data"]["email_token"]
        user.subscriptionDate = datetime.now().date()
        user.is_subscribed = True
        user.save()

        return True
    except Subscribers.DoesNotExist:
        Subscribers.objects.create(
            user=user,
            subscription_code=info["subscription_code"],
            status="active",
        )
        _subscriptionService(data)
    except User.DoesNotExist:
        return False
    except:
        return False


def check_date(provided_date_str: str, sub_code: str) -> bool:
    current_date = datetime.now()
    provided_date = datetime.fromisoformat(provided_date_str.replace("Z", "+00:00"))
    data = paystack.subscription.fetch(sub_code)
    return current_date.date() == provided_date.date()
