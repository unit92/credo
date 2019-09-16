from django.db import models
from django.contrib.auth.models import User


class Composer(models.Model):
    name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    name = models.TextField()
    composer = models.ForeignKey(
        Composer, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.composer.name}'


class MEI(models.Model):
    data = models.FileField(upload_to='mei_files')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'MEI object created at {self.created_at}'


class Edition(models.Model):
    name = models.TextField()
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    mei = models.ForeignKey(MEI, on_delete=models.SET_NULL, null=True)
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.song.name} - {self.uploader}'


class Revision(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mei = models.ForeignKey(MEI, on_delete=models.CASCADE)
    editions = models.ManyToManyField(Edition)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def song(self):
        return list({x.song for x in self.editions.all()})[0]

    def __str__(self):
        return f'Revision on {self.song()}'


class Comment(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mei_element_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment on {self.revision} by {self.user}'
