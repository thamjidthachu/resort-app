from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Service, File, Review


# Register your models here.


class FileInline(admin.TabularInline):
    model = File
    extras = 3


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'self_id', 'content_type')
    list_filter = ['content_type', 'user']


class ServiceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FileInline, ]
    list_display = ('name', 'create_time',)
    readonly_fields = ('create_time',)


admin.site.register(Service, ServiceAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(File)
