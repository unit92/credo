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
    data = models.BinaryField()
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


class Comment(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    position = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment on {self.edition} by {self.user}'


class Revision(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mei = models.ForeignKey(MEI, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def editions(self):
        return [x.edition for x in
                EditionRevision.objects.filter(revision=self)]

    def __str__(self):
        editions = self.editions()
        if len(editions) > 0:
            return f'Revision on {list(self.editions())} by {self.user}'
        else:
            return f'Revision by {self.user}'


class EditionRevision(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)

    def __str__(self):
        return f'Revision on {self.edition} by {self.revision.user}'
