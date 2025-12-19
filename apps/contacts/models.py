from django.db import models

from utils.abstract_models import TimeStampedModel

# Create your models here.


class ContactMessage(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    preferred_dates = models.CharField(max_length=512, null=True, blank=True)
    number_of_guests = models.IntegerField(null=True, blank=True)
    message = models.TextField()
    def __str__(self):
        return self.first_name