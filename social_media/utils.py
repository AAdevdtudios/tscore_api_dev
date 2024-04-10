from google.auth.transport import requests
from google.oauth2 import id_token
from account.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
import datetime


class GoogleAuth:
    @staticmethod
    def validate(access_token):
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request())
            if "accounts.google.com" in id_info["iss"]:
                return id_info

        except Exception as e:
            return "Token is invalid"


def login_user(email, password):
    if email is None:
        raise AuthenticationFailed("Email is empty")
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return {"message": "User password is incorrect", "status_code": 400}

        if not user.is_verified:
            return {"message": "User is not verified", "status_code": 400}

        user_tokens = user.tokens()
        user.lastLogin = datetime.datetime.now()
        user.save()

        return {
            "email": user.email,
            "full_name": user.get_full_name,
            "access_token": user_tokens.get("access"),
            "refresh_token": user_tokens.get("refresh"),
            "status_code": 200,
            "message": "User logged in",
        }
    except User.DoesNotExist:
        return {"message": "User doesn't exist", "status_code": 400}


def register_social_user(provider, email, first_name, last_name):
    user = User.objects.filter(email=email)
    if user.exists():
        if provider == user[0].auth_provider:
            auth = login_user(
                email=email,
                password=settings.SOCIAL_AUTH_PASSWORD,
            )

            return auth
        else:
            raise AuthenticationFailed(
                detail=f"Please continue with your {user[0].auth_provider}"
            )
    else:
        new_user = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": settings.SOCIAL_AUTH_PASSWORD,
        }
        register_user = User.objects.create_user(**new_user)
        register_user.auth_provider = provider
        register_user.is_verified = True
        register_user.save()
        user_tokens = login_user(email=email, password=settings.SOCIAL_AUTH_PASSWORD)

        return user_tokens
