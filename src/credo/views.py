from django.http import HttpResponse
from django.shortcuts import render
from .models import Comment, Edition, MEI, Revision, Song


def index(request):
    return render(request, 'message.html', {
        'message': 'Welcome to Credo.',
    })


def song_list(request):
    return render(request, 'song_list.html', {
        'songs': Song.objects.all(),
    })


def song(request, song_id):
    song = Song.objects.get(id=song_id)
    editions = Edition.objects.filter(song=song)
    revisions = Revision.objects.filter(editions__in=editions)
    return render(request, 'song.html', {
        'song': song,
        'editions': editions,
        'revisions': revisions,
    })


def edition(request, song_id, edition_id):
    song = Song.objects.get(id=song_id)
    edition = Edition.objects.get(id=edition_id, song=song)
    return render(request, 'render.html', {
        'to_render': edition,
    })


def revision(request, song_id, revision_id):
    song = Song.objects.get(id=song_id)
    revision = Revision.objects.get(id=revision_id, editions__song=song)
    return render(request, 'render.html', {
        'to_render': revision,
        'comments': True
    })


def revision_comments(request, revision_id):
    revision = Revision.objects.get(id=revision_id)
    comments = Comment.objects.filter(revision=revision)

    response = HttpResponse()
    response['Content-Type'] = 'application/json'
    json = ''
    json += '{'
    for comment in comments:
        json += f'"{comment.mei_element_id}": "{comment.text}",'
    json = json[:-1]
    json += '}'
    response.write(json)
    return response


def mei(request, mei_id):
    mei = MEI.objects.get(id=mei_id)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=file.mei'
    with mei.data.open() as f:
        response.write(f.read())
    return response
