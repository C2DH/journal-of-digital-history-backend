# Generated by Django 3.1.3 on 2021-05-17 10:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0007_article_issue'),
    ]

    operations = [
        migrations.RenameField(
            model_name='issue',
            old_name='title',
            new_name='name',
        ),
    ]