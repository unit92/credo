# Generated by Django 2.2.4 on 2019-10-14 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo', '0002_dbseed'),
    ]

    operations = [
        migrations.AddField(
            model_name='revision',
            name='name',
            field=models.TextField(blank=True, default=None, null=True)
        )
    ]
