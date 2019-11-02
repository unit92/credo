from django.http import HttpResponse, \
                        HttpResponseBadRequest, \
                        HttpResponseForbidden, \
                        JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.contrib.auth import login as auth_login, authenticate

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.contrib import messages

import base64
import json
import lxml.etree as et

from credo.utils.mei.tree_comparison import TreeComparison
from credo.utils.mei.measure_utils import merge_measure_layers
from credo.utils.mei.resolve_utils import is_resolved

from .models import Comment, Edition, MEI, Revision, Song

from .forms import SignUpForm

# Signal used to send message data upon the logout of user
@receiver(user_logged_out)
def on_user_logout(sender, request, **kwargs):
    messages.add_message(request, messages.SUCCESS, 'Logout Successful',
                         extra_tags='logout')


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

    if request.user.is_authenticated:
        revisions = Revision.objects.filter(
            editions__in=editions, user=request.user
        ).distinct('id')
    else:
        revisions = []

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
    editions = Edition.objects.filter(song=song, mei__normalised=True)
    if request.user.is_authenticated:
        revisions = Revision.objects.filter(
            editions__in=editions,
            mei__normalised=True,
            user=request.user
        ).distinct('id')
    else:
        revisions = []

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


def edition(request, edition_id):
    try:
        edition_id = int(edition_id)
    except ValueError:
        return HttpResponseBadRequest()

    edition = Edition.objects.get(id=edition_id)
    song = edition.song
    breadcrumbs = [
        {
            'text': 'Songs',
            'url': '/songs'
        },
        {
            'text': song.name,
            'url': f'/songs/{song.id}'
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
    def get(self, request, revision_id):
        try:
            revision_id = int(revision_id)
        except ValueError:
            return HttpResponseBadRequest()

        revision = Revision.objects.get(id=revision_id)
        song = revision.editions.all()[0].song
        breadcrumbs = [
            {
                'text': 'Songs',
                'url': '/songs'
            },
            {
                'text': song.name,
                'url': f'/songs/{song.id}'
            },
            {
                'text': revision.name or "Untitled Revision",
            }
        ]
        return render(request, 'revision.html', {
            'revision': revision,
            'comments': True,
            'resolved': revision.mei.normalised,
            'authenticated': request.user.is_authenticated,
            'save_url': f'/revisions/{revision_id}',
            'revision_id': revision_id,
            'breadcrumbs': breadcrumbs
        })

    def post(self, request, revision_id):

        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        try:
            revision_id = int(revision_id)
        except ValueError:
            return HttpResponseBadRequest()

        data = json.loads(request.body)
        comments = data['comments']
        mei = data['mei']
        mei_tree = et.XML(mei)

        revision = Revision.objects.get(id=revision_id)

        # Delete existing comments
        revision.comment_set.all().delete()

        for comment in comments:
            Comment(revision_id=revision_id,
                    text=comments[comment],
                    user=request.user,
                    mei_element_id=comment).save()

        # This assumes that once the MEI is resolved, there
        # is no way for it to be un-resolved.
        if not revision.mei.normalised:
            revision.mei.normalised = is_resolved(mei_tree)

        revision.mei.data.save('mei', ContentFile(mei))
        revision.mei.save()

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

    if not meis[0].normalised or not meis[1].normalised:
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


@require_http_methods(['POST'])
def merge_measure_layers_json(request):
    if request.content_type != 'application/json':
        return HttpResponseBadRequest(content_type='application/json')

    json_data = json.loads(request.body)
    try:
        measure = json_data['content']['mei']['detail']
        measure = str(base64.b64decode(measure), encoding='utf-8')
    except KeyError:
        return HttpResponseBadRequest(content_type='application/json')

    measure_tree = et.XML(measure)

    try:
        merged_measure_tree = merge_measure_layers(measure_tree)
    except ValueError:
        data = {
            'content': {
                'resolved': 'false'
            }
        }
        return HttpResponse(
            json.dumps(data),
            content_type='application/json'
        )

    merged_measure = et.tostring(merged_measure_tree, encoding='utf-8')
    measure_b64 = str(base64.b64encode(merged_measure), encoding='utf-8')

    data = {
        'content': {
            'mei': {
                'detail': measure_b64,
                'encoding': 'base64'
            },
            'resolved': 'true'
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
        # Ensure the MEI we are copying is normalised.
        if not meis[0].normalised:
            return HttpResponseBadRequest(content_type='application/json')

        # Ensure we normalise before saving
        new_mei.normalised = True

        # copy if just revising a single MEI
        file_content = ContentFile(meis[0].data.file.read())
        new_mei.data.save('mei', file_content)

        # IMPORTANT - must close the file, otherwise Django breaks
        meis[0].data.file.close()

    elif len(meis) == 2:
        # Ensure the MEIs we are generating the diff from are normalised
        if not meis[0].normalised or not meis[1].normalised:
            return HttpResponseBadRequest(content_type='application/json')

        # Do not normalise, since we are making a revision from a comparison.
        # Normalisation occurs after resolving the revision.
        new_mei.normalised = False

        # Compare
        engine = TreeComparison()
        out_meis = engine.compare_meis(meis[0], meis[1])
        diff, *sources = [et.tostring(mei, encoding='utf-8')
                          for mei in out_meis]
        new_mei.data.save('mei', ContentFile(diff))
    else:
        return HttpResponseBadRequest(content_type='application/json')

    new_mei.save()

    new_revision = Revision(user=request.user,
                            mei=new_mei)
    new_revision.save()
    new_revision.editions.set(base_editions)
    new_revision.save()

    return redirect(f'/revisions/{new_revision.id}')


@require_http_methods(['POST', 'GET'])
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            sign_up = form.save()
            # This line hashes the password
            sign_up.set_password(sign_up.password)
            sign_up.save()

            # Make user login upon signup
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')

            # Authenticate form detail & login if it returns User model
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                auth_login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def download_revision(request, revision_id):
    revision = Revision.objects.get(id=revision_id)
    if not (request.user.is_authenticated and revision.user == request.user):
        return HttpResponseForbidden()
    song = revision.editions.all()[0].song
    if revision.name:
        filename = f'{revision.name} - {song.name}.mei'
    else:
        filename = f'Untitled Revision - {song.name}.mei'
    response = HttpResponse(revision.mei.data, content_type='text/xml')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_edition(request, edition_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    edition = Edition.objects.get(id=edition_id)
    song = edition.song
    if edition.name:
        filename = f'{edition.name} - {song.name}.mei'
    else:
        filename = f'Untitled Revision - {song.name}.mei'
    response = HttpResponse(edition.mei.data, content_type='text/xml')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def page_not_found(request, exception):
    return render(
        request,
        'error.html',
        {
            'message': 'Sorry, we couldn\'t find what you were looking for.'
        },
        status=404
    )


def server_error(request):
    return render(
        request,
        'error.html',
        {
            'message': 'Uh oh. Something went wrong on our end.'
        },
        status=500
    )


def wildwebmidi_data(request):
    with open('credo/static/credo/midi/wildwebmidi.data', 'rb') as f:
        data = f.read()
    file_to_send = ContentFile(data)
    response = HttpResponse(file_to_send, 'application/x-gzip')
    response['Content-Length'] = file_to_send.size
    response['Content-Disposition'] = 'attachment; filename="wildwebmidi.data"'
    return response
