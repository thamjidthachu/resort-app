from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from apps.authentication.models import User


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('email',)

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
    

class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = ('full_name', 'username', 'email', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active',)

    admin_for_add_users = 'admin@view.com'

    def get_queryset(self, request):
        return User.objects.all()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.email if request.user.email == self.admin_for_add_users else None

        if is_superuser:
            form.base_fields['groups'].widget = forms.HiddenInput()


        return form

    fieldsets = (
        (None, {'fields': (
            'avatar','email', "username", "gender", 'phone', 'full_name',)}),
        ('Permissions', {'fields': ('is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        ('User Info', {
            'classes': ('wide',),
            'fields': ('full_name', 'email', 'password', 'username', "gender", 'phone',)}
         ),
        ('Signature', {
            'classes': ('wide',),
            'fields': ('avatar',)
        })
    )

    search_fields = ('email',)
    ordering = ('email',)


# Re-register UserAdmin
admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
