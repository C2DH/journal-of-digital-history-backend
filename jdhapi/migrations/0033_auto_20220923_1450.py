# Generated by Django 3.2.14 on 2022-09-23 12:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jdhapi', '0032_auto_20220922_1400'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallOfPaper',
            fields=[
                ('id', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250)),
                ('deadline_abstract', models.DateTimeField(blank=True, null=True)),
                ('deadline_article', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='abstract',
            name='call_paper',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jdhapi.callofpaper'),
        ),
    ]
