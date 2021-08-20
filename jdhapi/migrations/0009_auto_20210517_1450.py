# Generated by Django 3.1.3 on 2021-05-17 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0008_auto_20210517_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='data',
            field=models.JSONField(blank=True, default=dict, help_text='JSON format', verbose_name='data contents'),
        ),
        migrations.AddField(
            model_name='issue',
            name='data',
            field=models.JSONField(blank=True, default=dict, help_text='JSON format', verbose_name='data contents'),
        ),
    ]