from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from .models import Comment, Edition, MEI, Revision, Song

import json


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


@require_POST
def add_revision(request, song_id):
    body = json.loads(request.body)

    mei_file = ContentFile(body['mei'])
    mei_object = MEI()
    mei_object.data.save('mei', mei_file)
    mei_object.save()

    # TODO: save the revision
    #  - can't do this until we have edition data

    '''
    revision_object = Revision()
    revision_object.mei = mei_object
    revision_object.song_id = song_id
    # revision_object.user =  # who knows lmao
    '''

    # TODO: save the comments
    #  - can't do this until we save the revisions

    '''
    for mei_elem in body['comments']:
        comment = Comment()
        comment.mei_element_id = mei_elem
        comment.text = body['comments'][mei_elem]
        comment.revision = revision_object
        # revision_object.user =  # who knows lmao
    '''

    response = HttpResponse()
    response.write(f'/songs/{song_id}')
    return response

@require_POST
def add_revision_comment(request, revision_id):
    body = json.loads(request.body)
    comment = Comment()
    comment.text = body['text']
    comment.mei_element_id = body['elementId']
    comment.save()
    return JsonResponse({'ok': True})


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

    """
    yeah, this is big brain time
    https://i.kym-cdn.com/entries/icons/original/000/030/525/cover5.png
    """
    return JsonResponse({
        comment.mei_element_id: comment.text
        for comment in comments
    })


def mei(request, mei_id):
    mei = MEI.objects.get(id=mei_id)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=file.mei'
    with mei.data.open() as f:
        response.write(f.read())
    return response
