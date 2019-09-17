from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import json
from .models import Edition, MEI, Revision, Song


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
        'to_render': revision
    })


def mei(request, mei_id):
    mei = MEI.objects.get(id=mei_id)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=file.mei'
    with mei.data.open() as f:
        response.write(f.read())
    return response


@require_http_methods(['GET'])
def diff(request):
    diff_only = request.GET.get('diffonly')
    sources = request.GET.getlist('s')
    print(diff_only)
    print(sources)
    data = {
        'content': {
            'name': 'diff',
            'details': '',
            'encoding': 'base64'
        }
    }
    return HttpResponse(json.dumps(data), content_type='application/json')
