# Generated by Django 3.1.3 on 2021-06-11 16:30

from django.db import migrations, models
import jdhapi.models.abstract


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0017_issue_pid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstract',
            name='pid',
            field=models.CharField(db_index=True, default=jdhapi.models.abstract.create_short_url, max_length=255, unique=True),
        ),
    ]
