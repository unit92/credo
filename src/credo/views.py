from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import lxml.etree as et
import json
import base64
from credo.utils.mei.tree_comparison import TreeComparison


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
    with mei.data.open() as f:
        mei_data = f.read()
    mei_data = str(base64.b64encode(mei_data), encoding='utf-8')
    data = {
        'content': {
            'mei': {
                'detail': mei_data,
                'encoding': 'base64'
            }
        }
    }
    return HttpResponse(json.dumps(data), content_type='application/json')


def compare(request):
    source_ids = request.GET.getlist('s')

    # TODO Nicer rendering for bad source ids
    try:
        source_ids = [int(s) for s in source_ids]
    except ValueError:
        return HttpResponseBadRequest()

    return render(request, 'compare.html', {
        'sources': [{'id': s} for s in source_ids]
    })


@require_http_methods(['GET'])
def diff(request):
    sources = request.GET.getlist('s')

    try:
        sources = [int(s) for s in sources]
    except ValueError:
        return HttpResponseBadRequest(content_type='application/json')

    try:
        meis = [MEI.objects.get(id=s) for s in sources]
    except MEI.DoesNotExist:
        return HttpResponseBadRequest(content_type='application/json')

    if len(meis) != 2:
        return HttpResponseBadRequest(content_type='application/json')

    engine = TreeComparison()
    out_meis = engine.compare_meis(meis[0], meis[1])
    diff, *sources = [et.tostring(mei, encoding='utf-8') for mei in out_meis]
    diff = str(base64.b64encode(diff), encoding='utf-8')
    sources = [
        {
            'detail': str(base64.b64encode(s), encoding='utf-8'),
            'encoding': 'base64'
        }
        for s in sources
    ]

    data = {
        'content': {
            'diff': {
                'detail': diff,
                'encoding': 'base64'
            },
            'sources': sources
        }
    }
    return HttpResponse(json.dumps(data), content_type='application/json')
