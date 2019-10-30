import os
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from utils.mei.mei_transformer import MeiTransformer


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
    normalised = models.BooleanField(default=True)

    def __str__(self):
        file_id = os.path.split(self.data.name)[-1].split("_")[-1]
        return f'MEI object {file_id} created at {self.created_at}'


@receiver(post_save, sender=MEI)
def normalise_callback(sender, instance, *args, **kwargs):
    mei_file = instance.data.file.open()
    transformer = MeiTransformer.from_xml_file(mei_file)

    if instance.normalised:
        print('normalised')
        transformer.normalise()
        id_map = transformer.get_id_map()
        print(id_map)
        # get the comments which need to be re-keyed
        revision_set = instance.revision_set.all()
        print(revision_set)
        relevant_comments = Comment.objects.filter(
                revision__in=revision_set,
                mei_element_id__in=id_map)
        print(relevant_comments)
        for comment in relevant_comments:
            print(comment.mei_element_id, id_map[comment.mei_element_id])
            comment.mei_element_id = id_map[comment.mei_element_id]
            comment.save()
    else:
        transformer.remove_metadata()

    transformer.save_xml_file(instance.data.name)


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
    name = models.TextField(default=None, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mei = models.ForeignKey(MEI, on_delete=models.CASCADE)
    editions = models.ManyToManyField(Edition)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def song(self):
        return list({x.song for x in self.editions.all()})[0]

    def __str__(self):
        return f'{self.name or "Untitled Revision"} - {self.song().name}'


class Comment(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mei_element_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment on {self.revision} by {self.user}'
