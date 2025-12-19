from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager

from utils import GenderChoices
from utils.abstract_models import ActiveModel


class UserManager(BaseUserManager):
    """
    class manager for providing a User(AbstractBaseUser) full control
    on these objects to create all types of User and these roles.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        pass data  to '_create_user' for creating normal_user .
        """
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        pass data to '_create_user' for creating super_user .
        """
        if email is None:
            raise TypeError('Users must have an email address.')

        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, ActiveModel):
    """
    create class User from Abstraction and Permissions (from low_level) to give us
    full control to create user with role and other options not include in normal user
    """
    username = models.CharField(max_length=50)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(db_index=True, unique=True)
    phone = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True, null=True)
    avatar = models.FileField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)

    # For password reset
    reset_token = models.CharField(max_length=64, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'gender']

    objects = UserManager()

    def __str__(self):
        return self.email
