# Generated by Django 3.2.14 on 2022-09-02 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0028_auto_20220729_1053'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='cover_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]