import pyotp
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from logics.utils import send_email


# import resend
# import os

# resend.api_key = os.environ["RESEND_KEY"]
from .models import OneTimePassword, User

confirm_user_email = """
Hi [name],

Thanks for getting started with our [customer portal]!

We need a little more information to complete your registration, including a confirmation of your email address.

Click below to confirm your email address:

[link]

If you have problems, please paste the above URL into your web browser.
"""


def send_verification_email(
    email: str,
    data: dict,
    subject: str = "Verify Account",
    render: str = "verification-email.html",
):
    html_content = render_to_string(render, data)
    send_email(email=email, subject=subject, html=html_content)


def send_otp(email: str):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=1800)
    otp = totp.now()
    valid_date = datetime.now() + timedelta(minutes=30)

    try:
        user = User.objects.get(email=email)
        get_otp = OneTimePassword.objects.get(user=user)
        get_otp.date = str(valid_date)
        get_otp.code = otp
        get_otp.secrete = totp.secret
        get_otp.save()
        send_verification_email(
            email=email,
            data={
                "otp": otp,
            },
            subject="One Time Password",
            render="otp.html",
        )
        # params = {
        #     "from": "Acme <onboarding@resend.dev>",
        #     "to": f"{email}",
        #     "subject": f"Send OTP to {email}",
        #     "html": f"<strong>Your {otp} is</strong>",
        # }
        # email = resend.Emails.send(params)

        return {
            "message": "OTP Sent to email",
            "status": 200,
        }
    except User.DoesNotExist:
        return {"message": "User doesn't exist", "status": 400}
    except OneTimePassword.DoesNotExist:
        OneTimePassword.objects.create(
            user=user, code=otp, date=str(valid_date), secrete=totp.secret
        )
        return {
            "otp": otp,
            "Secret": totp.secret,
            "valid_date": str(valid_date),
            "status": 200,
        }


def validate(otp: str, email: str):
    try:
        user = User.objects.get(email=email)
        get_user_otp_details = OneTimePassword.objects.get(code=otp)
        totp = pyotp.TOTP(get_user_otp_details.secrete, interval=60)

        # Is User verified
        if user.is_verified:
            return {"message": "User is already valid", "status": 400}

        # Does the user email match the email otp
        if user.email != get_user_otp_details.user.email:
            return {"message": "Invalid User Otp", "status": 400}

        # Has the otp expired
        valid_until = datetime.fromisoformat(get_user_otp_details.date)
        if valid_until < datetime.now():
            return {"message": "OTP has expired", "status": 400}
        totp = pyotp.TOTP(get_user_otp_details.secrete, interval=1800)

        # Does the OTP match the generated OTP
        if not totp.verify(otp=otp):
            return {"message": "Invalid Otp or has expired", "status": 400}

        user.is_verified = True
        user.is_active = True
        user.save()

        user_tokens = user.tokens()

        return {
            "message": {
                "access_token": user_tokens.get("access"),
                "refresh_token": user_tokens.get("refresh"),
            },
            "status": 200,
        }

    except User.DoesNotExist:
        return {"message": "User doesn't exist", "status": 400}
    except OneTimePassword.DoesNotExist:
        return {"message": "OTP doesn't exist", "status": 400}
