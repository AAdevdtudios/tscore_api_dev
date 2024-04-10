from rest_framework import serializers
from django.contrib.auth import authenticate
from account.models import User
from rest_framework.exceptions import AuthenticationFailed
import datetime
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, smart_bytes, force_str
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .utils import send_verification_email
from django.utils.translation import gettext_lazy as _
from logics.utils import CheckNextDueDate
from django.conf import settings


class ErrorValidation(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    isWebsite = serializers.BooleanField(default=False)
    notification_id = serializers.CharField(default="")

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "isWebsite",
            "notification_id",
        ]

    def validate(self, attrs):
        password = attrs.get("password", "")
        password2 = attrs.get("password2", "")

        if password != password2:
            raise serializers.ValidationError("Password doesn't match")
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            notification_id=validated_data["notification_id"],
        )

        return user


class ResendOneTimePasswordRequest(serializers.Serializer):
    email = serializers.EmailField(max_length=256)


class ValidateOneTimePasswordRequest(serializers.Serializer):
    email = serializers.EmailField(max_length=256)
    otp = serializers.CharField(max_length=10)


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=256, required=False)
    password = serializers.CharField(max_length=68, write_only=True)
    access_token = serializers.CharField(max_length=256, read_only=True)
    refresh_token = serializers.CharField(max_length=256, read_only=True)
    status_code = serializers.IntegerField(read_only=True)
    message = serializers.CharField(max_length=256, read_only=True)
    notification_id = serializers.CharField(max_length=256, default=None)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "access_token",
            "refresh_token",
            "status_code",
            "message",
            "notification_id",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        email = attrs.get("email")
        password = attrs.get("password")
        notification_id = attrs.get("notification_id")

        try:
            user = authenticate(request=request, email=email, password=password)
            if not user:
                raise AuthenticationFailed(
                    "Invalid credentials or your account hasn't been activated"
                )
            code = User.objects.get(email=email)
            if notification_id is not None:
                code.notification_id = notification_id
                code.save()
            if code.subscriptionCode:
                data = CheckNextDueDate(code.subscriptionCode)
                code.is_subscribed = data["is_subscribed"]
                code.email_token = data["email_token"]
                code.save()
            user_tokens = user.tokens()
            return {
                "access_token": user_tokens.get("access"),
                "refresh_token": user_tokens.get("refresh"),
                "message": "User logged in",
                "status_code": 200,
            }
        except User.DoesNotExist:
            return {"message": "User doesn't exist", "status_code": 400}


class SendVerifyToken(serializers.Serializer):
    email = serializers.EmailField(max_length=256)

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.is_verified:
                raise ErrorValidation("User already verified", status_code=400)

            uid = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get("request")
            site_domain = get_current_site(request=request).domain
            # absLink = f"http://{site_domain}/api/v1/auth/verify/{uid}/{token}"
            absLink = f"{settings.WEBSITEURL}/verifyuser/{uid}/{token}"
            data = {
                "url": absLink,
            }
            send_verification_email(email=user.email, data=data)

            return super().validate(attrs)
        else:
            raise serializers.ValidationError("User doesn't exist")


class PasswordResetRequest(serializers.Serializer):
    email = serializers.EmailField(max_length=256)

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get("request")
            # site_domain = get_current_site(request=request).domain
            # retrieve_lik = reverse(
            #     "password-reset-confirm", kwargs={"uidb64": uid64, "token": token}
            # )
            # absLink = f"http://{site_domain}{retrieve_lik}"
            absLink = f"{settings.WEBSITEURL}/password-reset/{uid64}/{token}"
            send_verification_email(
                email=email,
                subject="Password Reset",
                render="password-reset.html",
                data={
                    "url": absLink,
                },
            )
            return super().validate(attrs)
        else:
            raise serializers.ValidationError("User doesn't exist")


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    uidb64 = serializers.CharField(max_length=256, write_only=True)
    token = serializers.CharField(max_length=256, write_only=True)

    class Meta:
        fields = ["password", "password2", "uidb64", "token"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            password2 = attrs.get("password2")
            uidb64 = attrs.get("uidb64")
            token = attrs.get("token")

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("Reset link is invalid")
            if password != password2:
                raise AuthenticationFailed("Password doesn't match")
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            return AuthenticationFailed("Link is invalid")


class LogOutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_messages = {"bad_token": ("Token is invalid or has expired")}

    def validate(self, attrs):
        self.token = attrs.get("refresh_token")
        return super().validate(attrs)

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail("Bad token")


class UserDataSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=256)
    get_full_name = serializers.ReadOnlyField()
    subscriber_number = serializers.CharField(max_length=256, read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "get_full_name",
            "subscriber_number",
            "is_subscribed",
            "is_verified",
            "phone_number",
        ]
