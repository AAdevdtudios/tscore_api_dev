from paystackapi.paystack import Paystack
from datetime import datetime
from django.conf import settings
import resend
from firebase_admin import messaging
import requests

from google.oauth2 import service_account
from google.auth.transport.requests import Request

import firebase_admin
from firebase_admin import credentials

from core.settings import RESEND_KEY, API_FCM, INFOS, SCOPES
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

paystack_secret_key = settings.PAYSTACKSCKEY
resendKey = RESEND_KEY
paystack = Paystack(secret_key=paystack_secret_key)
resend.api_key = "re_2RTqXv6k_EcECn1Cuur6VY6hCvKxyeWcS"


def CreatePlan(interval: str, name: str, amount: int):
    data = {"name": name, "interval": interval, "amount": str(amount)}
    res = paystack.plan.create(**data)
    return res["data"]["plan_code"]


def CheckNextDueDate(code: str):
    data = paystack.subscription.fetch(code)
    print(data)

    email_token = data["data"]["email_token"]

    if data["data"]["status"] in ("complete", "non-renewing"):
        response = {
            "email_token": email_token,
            "is_subscribed": False,
        }
        return response
    response = {
        "email_token": email_token,
        "is_subscribed": True,
    }

    return response


from django.utils.html import strip_tags


def send_email(
    email: str,
    subject: str,
    html: str,
    # emailId: int | None,
) -> bool:
    msg = EmailMultiAlternatives(
        subject,
        strip_tags(html),
        settings.EMAIL_HOST_USER,
        [
            email,
        ],
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

    return True
    # params = {
    #     "from": "info <info@tscore.ng>",
    #     "to": [email],
    #     "subject": subject,
    #     "html": html,
    # }
    # resend.Emails.send(params)


def get_filename(filename, request):
    return filename.upper()


def _get_token() -> str:
    credentials = service_account.Credentials.from_service_account_info(
        INFOS, scopes=SCOPES
    )
    auth_req = Request()
    credentials.refresh(auth_req)
    return credentials.token


def send_notification(id, message, content):
    url = API_FCM
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "token": id,
            "notification": {
                "title": message,
                "body": content,
            },
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response)
