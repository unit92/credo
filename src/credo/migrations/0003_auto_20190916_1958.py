# Generated by Django 2.2.4 on 2019-09-16 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo', '0002_auto_20190916_1954'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='position',
        ),
        migrations.AddField(
            model_name='comment',
            name='mei_element_id',
            field=models.TextField(default='m-79'),
            preserve_default=False,
        ),
    ]
