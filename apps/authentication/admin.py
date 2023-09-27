from django.contrib import admin
from django.contrib.auth.models import Group

from django.contrib.auth.admin import UserAdmin

from .models import User


# Define a new User admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'is_staff', 'is_active', 'created_time')
    list_filter = ('citizen',)
    ordering = ('created_time',)

    fieldsets = (
        ('User Info', {
            'classes': ('wide',),
            'fields': ('avatar', 'age', 'gender', 'email', 'address', "contacts", "citizen",)}
         ),
        ('Other Info', {
            'classes': ('collapse',),
            'fields': ('is_staff', 'is_superuser',)}
         ),
    )
    add_fieldsets = (
        ('Other Info', {
            'classes': ('collapse',),
            'fields': ('is_staff', 'is_superuser',)}
         ),
    )


admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
