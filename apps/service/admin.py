from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Service, File, Comment, Advertisement, Favorite


# Register your models here.

class ImagesInline(admin.StackedInline):
    model = File
    extra = 0


class CommentsInline(GenericTabularInline):
    model = Comment
    fields = ['author', 'message', 'rating']
    readonly_fields = ['author', 'message', 'rating']
    can_delete = False
    verbose_name_plural = 'Comments'
    extra = 1

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ServiceAdmin(admin.ModelAdmin):
    inlines = [ImagesInline, CommentsInline]
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'price', 'unit', 'time',)
    readonly_fields = ('create_time',)


admin.site.register(Service, ServiceAdmin)
admin.site.register(Advertisement)
admin.site.register(Favorite)

