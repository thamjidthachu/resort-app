# Create your models here.
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from ckeditor.fields import RichTextField
from django.db.models.fields import DateTimeField
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
import re
import os

from apps.authentication.models import User
from utils import ActiveModel, TimeStampedModel


class Advertisement(TimeStampedModel, ActiveModel):
    title = models.CharField(max_length=256)
    file = models.FileField(upload_to="service_advertisement", max_length=256, null=True, blank=True)
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.title


class Service(TimeStampedModel, ActiveModel):
    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True, blank=True)
    synopsis = models.TextField(null=True)
    description = RichTextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=256)
    time = models.IntegerField()
    max_people = models.IntegerField()
    min_people = models.IntegerField()
    location = models.CharField(max_length=256)
    policy = RichTextField(null=True)
    create_time = DateTimeField(blank=True, auto_now_add=True)

    service_comment = GenericRelation('comment')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Service, self).save(*args, **kwargs)

    def get_review(self):
        return self.service_comment.all()


class File(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    images = models.FileField(upload_to="service_images", max_length=256)

    def __str__(self):
        return f'{str(self.service)} - {str(self.images)}'


class Comment(TimeStampedModel, ActiveModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0)
    message = models.CharField(max_length=256)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.message


class Favorite(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'service')

    def __str__(self):
        return f"{self.user.email} - {self.service.name}"
