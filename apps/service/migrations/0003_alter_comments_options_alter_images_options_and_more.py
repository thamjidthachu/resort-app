# Generated by Django 4.2.3 on 2023-07-22 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0002_rename_number_images_service_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comments',
            options={'verbose_name': 'comment'},
        ),
        migrations.AlterModelOptions(
            name='images',
            options={'verbose_name': 'image'},
        ),
        migrations.AlterModelOptions(
            name='services',
            options={'verbose_name': 'service'},
        ),
    ]