# Generated by Django 3.1.3 on 2021-07-14 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0019_auto_20210625_1039'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='binder_url',
            field=models.URLField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='notebook_path',
            field=models.CharField(blank=True, max_length=254, null=True),
        ),
    ]
