from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.validators import RegexValidator


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

    def create_superuser(self, email, password, **extra_fields):
        """
        pass data to '_create_user' for creating super_user .
        """
        if email is None:
            raise TypeError('Users must have an email address.')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )

    avatar = models.FileField(upload_to='avatar', blank=True, null=True)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(db_index=True, unique=True)
    address = models.CharField(max_length=200, default='')
    contacts = models.IntegerField(null=True)
    citizen = models.CharField(max_length=100, default='')
    created_time = models.DateTimeField(blank=True, auto_now_add=True)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    USERNAME_FIELD = 'email'

    objects = UserManager()

    def __str__(self):
        return str(self.email)
