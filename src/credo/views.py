from django.http import HttpResponse, \
                        HttpResponseBadRequest, \
                        HttpResponseForbidden, \
                        JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

import base64
import json
import lxml.etree as et

from credo.utils.mei.tree_comparison import TreeComparison
from .models import Comment, Edition, MEI, Revision, Song


def index(request):
    return render(request, 'index.html')


def song_list(request):
    breadcrumbs = [
        {
            'text': 'Songs',
        }
    ]
    return render(request, 'song_list.html', {
        'songs': Song.objects.all(),
        'breadcrumbs': breadcrumbs
    })


def song(request, song_id):
    song = Song.objects.get(id=song_id)
    editions = Edition.objects.filter(song=song)
    revisions = Revision.objects.filter(editions__in=editions).distinct('id')
    breadcrumbs = [
        {
            'text': 'Songs',
            'url': '/songs'
        },
        {
            'text': song.name,
        }
    ]
    return render(request, 'song.html', {
        'song': song,
        'editions': editions,
        'revisions': revisions,
        'breadcrumbs': breadcrumbs
    })


def song_compare_picker(request, song_id):
    song = Song.objects.get(id=song_id)
    editions = Edition.objects.filter(song=song)
    revisions = Revision.objects.filter(editions__in=editions).distinct('id')
    comparables = [{
        'id': f'e{edition.id}',
        'name': edition.name
    } for edition in editions] + [{
        'id': f'r{revision.id}',
        'name': revision
    } for revision in revisions]
    return render(request, 'song_compare_picker.html', {
        'song': song,
        'comparables': comparables,
        'breadcrumbs': [{
            'text': 'Songs',
            'url': '/songs'
        }, {
            'text': song.name,
            'url': f'/songs/{song.id}'
        }, {
            'text': 'Compare'
        }]
    })


def edition(request, song_id, edition_id):
    song = Song.objects.get(id=song_id)
    edition = Edition.objects.get(id=edition_id, song=song)
    breadcrumbs = [
        {
            'text': 'Songs',
            'url': '/songs'
        },
        {
            'text': song.name,
            'url': f'/songs/{song_id}'
        },
        {
            'text': edition.name,
        }
    ]
    return render(request, 'edition.html', {
        'authenticated': request.user.is_authenticated,
        'edition': edition,
        'breadcrumbs': breadcrumbs
    })


@require_http_methods(['POST'])
def add_revision_comment(request, revision_id):
    body = json.loads(request.body)
    comment = Comment()
    comment.text = body['text']
    comment.mei_element_id = body['elementId']
    comment.save()
    return JsonResponse({'ok': True})


class RevisionView(View):

    def get(self, request, song_id, revision_id):
        song = Song.objects.get(id=song_id)
        revision = Revision.objects.filter(
                id=revision_id, editions__song=song).distinct('id')[0]
        breadcrumbs = [
            {
                'text': 'Songs',
                'url': '/songs'
            },
            {
                'text': song.name,
                'url': f'/songs/{song_id}'
            },
            {
                'text': revision.name or "Untitled Revision",
            }
        ]
        return render(request, 'revision.html', {
            'revision': revision,
            'comments': True,
            'authenticated': request.user.is_authenticated,
            'save_url': f'/songs/{song_id}/revisions/{revision_id}',
            'breadcrumbs': breadcrumbs
        })

    def post(self, request, song_id, revision_id):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        data = json.loads(request.body)
        comments = data['comments']

        revision = Revision.objects.get(id=revision_id)

        # Delete existing comments
        revision.comment_set.all().delete()

        for comment in comments:
            Comment(revision_id=revision_id,
                    text=comments[comment],
                    user=request.user,
                    mei_element_id=comment).save()

        return JsonResponse({'ok': True})


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
    edition_ids = request.GET.getlist('e')
    revision_ids = request.GET.getlist('r')
    try:
        edition_ids = [int(e) for e in edition_ids]
        revision_ids = [int(r) for r in revision_ids]
    except ValueError:
        return HttpResponseBadRequest()

    edition_queries = [f'e={e}' for e in edition_ids]
    revision_queries = [f'r={r}' for r in revision_ids]

    editions = [Edition.objects.get(id=edition_id) for edition_id in
                edition_ids]
    revisions = [Revision.objects.get(id=revision_id) for revision_id in
                 revision_ids]

    title = 'Comparison'
    song = None
    if len(editions):
        edition = Edition.objects.get(id=edition_ids[0])
        song = edition.song
    elif len(revisions):
        revision = Revision.objects.get(id=revision_ids[0])
        song = revision.song()

    if song:
        title = song.name

    querystring = '&'.join(edition_queries + revision_queries)
    mei_ids = [edition.mei.id for edition in editions] + \
              [revision.mei.id for revision in revisions]
    mei_queries = [f's={id}' for id in mei_ids]
    mei_query_string = '&'.join(mei_queries)
    mei_url = f'/diff?{mei_query_string}'

    return render(request, 'song_compare.html', {
        'authenticated': request.user.is_authenticated,
        'mei_url': mei_url,
        'querystring': querystring,
        'title': title,
        'breadcrumbs': [{
            'text': 'Songs',
            'url': '/songs'
        }, {
            'text': song.name,
            'url': f'/songs/{song.id}'
        }, {
            'text': 'Compare'
        }]
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


@require_http_methods(['GET'])
def make_revision(request):
    edition_ids = request.GET.getlist('e')
    revision_ids = request.GET.getlist('r')

    try:
        edition_ids = [int(id) for id in edition_ids]
        revision_ids = [int(id) for id in revision_ids]
    except ValueError:
        return HttpResponseBadRequest(content_type='application/json')

    editions = [Edition.objects.get(id=edition_id) for edition_id in
                edition_ids]
    revisions = [Revision.objects.get(id=revision_id) for revision_id in
                 revision_ids]

    # editions used to build this revision
    base_editions = set(editions)
    for revision in revisions:
        base_editions = base_editions.union(set(revision.editions.all()))

    meis = [edition.mei for edition in editions] + \
           [revision.mei for revision in revisions]

    file_content = None

    new_mei = MEI()

    if len(meis) == 1:
        # copy if just revising a single MEI
        file_content = ContentFile(meis[0].data.file.read())
        print(type(meis[0].data.file.read()))
        new_mei.data.save('mei', file_content)

        # IMPORTANT - must close the file, otherwise Django breaks
        meis[0].data.file.close()
    elif len(meis) == 2:
        # compare if there are two MEIs
        engine = TreeComparison()
        out_meis = engine.compare_meis(meis[0], meis[1])
        diff, *sources = [et.tostring(mei, encoding='utf-8')
                          for mei in out_meis]
        new_mei.data.save('mei', ContentFile(diff))
    else:
        return HttpResponseBadRequest(content_type='application/json')

    # duplicate the mei
    new_mei.save()

    new_revision = Revision(user=request.user,
                            mei=new_mei)
    new_revision.save()
    new_revision.editions.set(base_editions)
    new_revision.save()

    return redirect(
            f'/songs/{new_revision.song().id}/revisions/{new_revision.id}')


def login(request):
    return render(request, 'login.html')
