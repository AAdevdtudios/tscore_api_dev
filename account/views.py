from django.shortcuts import render, get_object_or_404
from rest_framework.generics import GenericAPIView

from logics.utils import CheckNextDueDate
from .serializer import (
    SendVerifyToken,
    UserRegisterSerializer,
    ResendOneTimePasswordRequest,
    ValidateOneTimePasswordRequest,
    LoginSerializer,
    PasswordResetRequest,
    SetNewPasswordSerializer,
    LogOutSerializer,
    UserDataSerializer,
    ErrorValidation,
)
from rest_framework.response import Response
from rest_framework import status
from .utils import send_otp, validate
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.permissions import IsAuthenticated

from .models import User

# Create your views here.


# Send OTP
class ResendOtp(GenericAPIView):
    serializer_class = ResendOneTimePasswordRequest

    # send new Otp
    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.error_messages, status=400)

        info = serializer.data
        sent_data = send_otp(info["email"])
        return Response(sent_data, status=sent_data["status"])


class VerifyOtp(GenericAPIView):
    serializer_class = ValidateOneTimePasswordRequest

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.error_messages, status=400)

        info = serializer.data
        valid = validate(
            otp=info["otp"],
            email=info["email"],
        )
        return Response(valid, status=valid["status"])


class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            # This would be sent if it was Website
            serializer.save()
            user = serializer.data
            if serializer.validated_data["isWebsite"]:
                data = {"email": user["email"]}
                send_verification = SendVerifyToken(
                    data=data, context={"request": request}
                )
                send_verification.is_valid(raise_exception=True)
            else:
                # This would be sent if it is mobile
                send_otp(user["email"])

            first_name = user["first_name"]

            # Send email function
            return Response(
                {
                    # "data": user,
                    "message": f"Hi {first_name} thanks for signing up a pass code has been sent to your email",
                },
                status=200,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View to verify user
class VerifyUserToken(GenericAPIView):
    serializer_class = SendVerifyToken

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            return Response({"message": serializer.data}, status=200)
        except ErrorValidation as e:
            return Response({"message": str(e)}, status=e.status_code)

    def get(self, request, uid, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)
            if user.is_verified:
                return Response({"message": "User is already verified"}, status=400)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"message": "Token is invalid or as expired"}, status=400
                )
            user.is_verified = True
            user.is_active = True
            user_tokens = user.tokens()
            user.save()
            return Response(
                {
                    "message": {
                        "access_token": user_tokens.get("access"),
                        "refresh_token": user_tokens.get("refresh"),
                    }
                },
                status=200,
            )
        except DjangoUnicodeDecodeError:
            Response({"message": "Token is invalid or as expired"}, status=400)


class LoginUser(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=serializer.data["status_code"])


class PasswordResetView(GenericAPIView):
    serializer_class = PasswordResetRequest

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response({"message": serializer.data}, status=200)


class PasswordResetConfirmView(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"message": "Token is invalid or as expired"}, status=400
                )
            return Response({"message": "Token is valid"}, status=200)
        except DjangoUnicodeDecodeError:
            Response({"message": "Token is invalid or as expired"}, status=400)


class SetNewPasswordView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Password is set"}, status=200)


class LogOutView(GenericAPIView):
    serializer_class = LogOutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)


class GetData(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserDataSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_object_or_404(User, email=request.user)
        data = CheckNextDueDate(user.subscriptionCode)
        user.is_subscribed = data["is_subscribed"]
        user.email_token = data["email_token"]
        user.save()
        serializer = self.serializer_class(instance=user)

        return Response(data=serializer.data, status=200)
