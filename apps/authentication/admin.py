from django.contrib import admin
from django.contrib.auth.models import Group

from django.contrib.auth.admin import UserAdmin

from .models import User


# Define a new User admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email',)
    list_filter = ('citizen',)
    ordering = ('created_time',)


admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
