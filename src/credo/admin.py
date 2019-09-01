from django.contrib import admin

from .models import (Composer,
                     Song,
                     MEI,
                     Edition,
                     Comment,
                     Revision)


class ComposerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at', 'updated_at']


class SongAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'composer', 'created_at', 'updated_at']

class MEIAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at']


class EditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'song', 'uploader', 'created_at', 'updated_at']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'edition', 'user', 'created_at', 'updated_at']


class RevisionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at']


admin.site.register(Composer, ComposerAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(MEI, MEIAdmin)
admin.site.register(Edition, EditionAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Revision, RevisionAdmin)
