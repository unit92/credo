from django.http import HttpResponse, \
                        HttpResponseBadRequest, \
                        HttpResponseForbidden, \
                        JsonResponse
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

import base64
import json
import lxml.etree as et

from credo.utils.mei.tree_comparison import TreeComparison
from .models import Comment, Edition, MEI, Revision, Song

from .forms import SignUpForm


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
    return render(request, 'edition.html', {
        'authenticated': request.user.is_authenticated,
        'edition': edition
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
        revision = Revision.objects.get(id=revision_id, editions__song=song)
        return render(request, 'revision.html', {
            'revision': revision,
            'comments': True,
            'authenticated': request.user.is_authenticated,
            'save_url': f'/songs/{song_id}/revisions/{revision_id}'
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


@require_http_methods(['GET'])
def make_revision(request):
    editions = request.GET.getlist('e')

    # if not revising a single edition, return a Bad Request response
    if len(editions) != 1:
        return HttpResponseBadRequest(content_type='application/json')

    # only one edition to base revision from, no need to invoke diffing
    edition = Edition.objects.get(id=editions[0])

    # duplicate the mei
    new_mei = MEI()
    filecontent = ContentFile(edition.mei.data.file.read())
    new_mei.data.save('mei', filecontent)
    new_mei.save()

    # IMPORTANT - must close the file, otherwise Django breaks
    edition.mei.data.file.close()

    new_revision = Revision(user=request.user,
                            mei=new_mei)
    new_revision.save()
    new_revision.editions.set([edition])
    new_revision.save()

    return redirect(
            f'/songs/{new_revision.song().id}/revisions/{new_revision.id}')


def login(request):
    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
