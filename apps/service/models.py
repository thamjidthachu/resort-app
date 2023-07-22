# Create your models here.
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from ckeditor.fields import RichTextField
from apps.authentication.models import Costumer
from django.db.models.fields import DateTimeField
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType


class Services(models.Model):
    name = models.CharField(max_length=40)
    image = models.ImageField(upload_to="service_images", max_length=256)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = RichTextField(null=True)
    create_time = DateTimeField(blank=True, auto_now_add=True)
    service_comment = GenericRelation('comments')

    class Meta:
        verbose_name = "service"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Services, self).save(*args, **kwargs)


class Images(models.Model):
    service = models.ForeignKey(Services, on_delete=models.CASCADE)
    images = models.ImageField(upload_to="service_images", max_length=256)

    class Meta:
        verbose_name = "image"

    def __str__(self):
        return '%s - %s' % (str(self.service), str(self.images))


class Comments(models.Model):
    author = models.ForeignKey(Costumer, on_delete=models.CASCADE)
    message = models.CharField(max_length=256)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    comment_time = DateTimeField(auto_now_add=True, blank=True)
    comment = GenericRelation('comments')

    class Meta:
        verbose_name = "comment"

    def __str__(self):
        return self.message

