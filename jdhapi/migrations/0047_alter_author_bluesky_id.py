# Generated by Django 5.1.6 on 2025-05-08 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0046_alter_author_github_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='bluesky_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
