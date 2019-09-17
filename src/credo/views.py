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
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=file.mei'
    with mei.data.open() as f:
        response.write(f.read())
    return response


# TODO: Authenticate?
@require_http_methods(['GET'])
def diff(request):
    diff_only = request.GET.get('diffonly')
    sources = request.GET.getlist('s')

    try:
        sources = [int(sources[i]) for i in range(len(sources))]
    except ValueError:
        return HttpResponseBadRequest(content_type='application/json')

    print(diff_only)

    try:
        meis = [MEI.objects.get(id=sources[i]) for i in range(len(sources))]
    except MEI.DoesNotExist:
        return HttpResponseBadRequest(content_type='application/json')

    if len(meis) != 2:
        return HttpResponseBadRequest(content_type='application/json')

    engine = TreeComparison()
    out = engine.compare_meis(meis[0], meis[1])
    d, *s = [et.tostring(out[i], encoding='utf-8') for i in range(len(out))]
    d = str(base64.b64encode(d), encoding='utf-8')
    s = [{
            'details': str(base64.b64encode(s[i]), encoding='utf-8'),
            'encoding': 'base64'
        } for i in range(len(s))]

    data = {
        'content': {
            'diff': {
                'details': d,
                'encoding': 'base64'
            },
            'sources': s
        }
    }
    return HttpResponse(json.dumps(data), content_type='application/json')
