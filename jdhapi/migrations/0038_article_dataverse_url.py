# Generated by Django 3.2.14 on 2023-08-16 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0037_alter_abstract_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='dataverse_url',
            field=models.URLField(blank=True, help_text='Url to find here https://data.journalofdigitalhistory.org/', null=True),
        ),
    ]