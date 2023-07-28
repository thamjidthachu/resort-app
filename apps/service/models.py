# Create your models here.
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from ckeditor.fields import RichTextField
from apps.authentication.models import Costumer
from django.db.models.fields import DateTimeField
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType

STATUS = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]


class Service(models.Model):
    name = models.CharField(max_length=40)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    image = models.ImageField(upload_to="service_images", max_length=256)
    description = models.CharField(max_length=400)
    Body = RichTextField(null=True)
    create_time = DateTimeField(blank=True, auto_now_add=True)
    status = models.CharField(max_length=40, choices=STATUS)
    service_comment = GenericRelation('Review')

    class Meta:
        verbose_name = "service"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Service, self).save(*args, **kwargs)


class File(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="service_images", max_length=256)

    def __str__(self):
        return '%s - %s' % (str(self.service), str(self.image))


class Review(models.Model):
    user = models.ForeignKey(Costumer, on_delete=models.CASCADE)
    review = models.CharField(max_length=256)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    self_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'self_id')
    review_time = DateTimeField(auto_now_add=True, blank=True)
    review_replay = GenericRelation('Review')

    def __str__(self):
        return self.message

