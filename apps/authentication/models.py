from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models



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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(db_index=True, unique=True)
    avatar = models.FileField(upload_to='avatar', blank=True, null=True)
    age = models.IntegerField(null=True)
    address = models.CharField(max_length=200, default=None)
    contacts = models.IntegerField(null=True)
    citizen = models.CharField(max_length=100, default=None)
    created_time = models.DateTimeField(blank=True, auto_now_add=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    def __str__(self):
        return str(self.user)
