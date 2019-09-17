# Generated by Django 2.2.4 on 2019-09-15 09:28

import datetime
from django.utils import timezone
from django.db import migrations, models

#MIGRATE FUNCTIONS
def load_composers(apps, schema_editor):
    Composer = apps.get_model('credo', 'Composer')

    time = timezone.now()
    c1 = Composer(id=0, name='Craig Smith', created_at=time, updated_at=time)
    c1.save()

    c2 = Composer(id=1, name='Luke Tuthill', created_at=time, updated_at=time)
    c2.save()

    c3 = Composer(id=2, name='Joel Aquilina', created_at=time, updated_at=time)
    c3.save()

    c4 = Composer(id=3, name='Alex Mirrington', created_at=time, updated_at=time)
    c4.save()

def load_songs(apps, schema_editor):
    Song = apps.get_model('credo', 'Song')
    Composer = apps.get_model('credo', 'Composer')

    time = timezone.now()
    composer = Composer.objects.get(id=0)
    s1 = Song(id=0, name='JS Standard', composer=composer, created_at=time,
            updated_at=time)
    s1.save()

    composer = Composer.objects.get(id=1)
    s2 = Song(id=1, name='Jingle Django', composer=composer, created_at=time,
            updated_at=time)
    s2.save()

    composer = Composer.objects.get(id=2)
    s3 = Song(id=2, name='Environment Song', composer=composer, created_at=time,
            updated_at=time)
    s3.save()

    composer = Composer.objects.get(id=3)
    s4 = Song(id=3, name='Diffing Song', composer=composer, created_at=time,
            updated_at=time)
    s4.save()


def load_mei(apps, schema_editor):
    MEI = apps.get_model('credo', 'MEI')

    time = timezone.now()
    m1 = MEI(id=0, data='./credo/migrations/seed_mei/SourceA.mei', created_at=time,
            updated_at=time)
    m1.save()

    m2 = MEI(id=1, data='./credo/migrations/seed_mei/SourceB.mei', created_at=time,
            updated_at=time)
    m2.save()

    m3 = MEI(id=2, data='./credo/migrations/seed_mei/SourceC.mei', created_at=time,
            updated_at=time)
    m3.save()

#ROLLBACK FUNCTIONS
def delete_composers(apps, schema_editor):
    Composer = apps.get_model('credo', 'Composer')
    Composer.objects.get(id=0).delete()
    Composer.objects.get(id=1).delete()
    Composer.objects.get(id=2).delete()
    Composer.objects.get(id=3).delete()

def delete_songs(apps, schema_editor):
    Song = apps.get_model('credo', 'Song')
    Song.objects.get(id=0).delete()
    Song.objects.get(id=1).delete()
    Song.objects.get(id=2).delete()
    Song.objects.get(id=3).delete()

def delete_mei(apps, schema_editor):
    MEI = apps.get_model('credo', 'MEI')
    MEI.objects.get(id=0).delete()
    MEI.objects.get(id=1).delete()
    MEI.objects.get(id=2).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('credo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_composers, delete_composers),
        migrations.RunPython(load_songs, delete_songs),
        migrations.RunPython(load_mei, delete_mei),
    ]
