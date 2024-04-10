from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from random import randrange

# from .models import User


class UserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            return ValueError(_("Please enter a valid email address"))

    def generate_random(self):
        random_number = randrange(1000000000, 9999999999)
        # check_unique = User.objects.filter(subscriber_number=random_number)

        return random_number

    def create_user(self, email, first_name, last_name, password, **extra_fields):
        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(_("An email address is required"))
        if not first_name:
            raise ValueError(_("First name is required"))
        if not last_name:
            raise ValueError(_("Last name is required"))

        user = self.model(
            email=email, first_name=first_name, last_name=last_name, **extra_fields
        )
        user.subscriber_number = str(self.generate_random())
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Is staff must be true for admin user"))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Is Superuser must be true for admin user"))

        user = self.create_user(email, first_name, last_name, password, **extra_fields)
        user.save(using=self._db)

        return user
