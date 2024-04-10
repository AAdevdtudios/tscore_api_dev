from django.urls import path
from .views import (
    RegisterUserView,
    ResendOtp,
    VerifyOtp,
    LoginUser,
    PasswordResetView,
    PasswordResetConfirmView,
    SetNewPasswordView,
    LogOutView,
    GetData,
    VerifyUserToken,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("data/", GetData.as_view(), name="GetData"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginUser.as_view(), name="login"),
    path("logout/", LogOutView.as_view(), name="logout"),
    # path("reset-password/", PasswordResetView.as_view(), name="reset-password"),
    path("verify/", VerifyUserToken.as_view(), name="Verify-User"),
    path("verify/<uid>/<token>", VerifyUserToken.as_view(), name="Verify-User"),
    # Previous method of what i did
    path("resendOtp/", ResendOtp.as_view(), name="Send-OTP"),
    path("validateOtp/", VerifyOtp.as_view(), name="Verify-OTP"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("set-new-password/", SetNewPasswordView.as_view(), name="set-new-password"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    # path("otp/<str:id>", ShowOTP.as_view(), name="OTP"),
]
